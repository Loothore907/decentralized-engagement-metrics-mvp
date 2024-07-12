# src/database/sql_db_manager.py

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLDBManager:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST")
        )
        self.cur = self.conn.cursor()
    def start_transaction(self):
        self.conn.autocommit = False

    def commit_transaction(self):
        self.conn.commit()
        self.conn.autocommit = True

    def rollback_transaction(self):
        self.conn.rollback()
        self.conn.autocommit = True

    def check_username_exists(self, twitter_username):
        query = "SELECT EXISTS(SELECT 1 FROM user_accounts WHERE twitter_username = %s)"
        self.cur.execute(query, (twitter_username,))
        return self.cur.fetchone()[0]

    def check_wallet_exists(self, wallet_address):
        query = "SELECT EXISTS(SELECT 1 FROM user_wallets WHERE wallet_address = %s)"
        self.cur.execute(query, (wallet_address,))
        return self.cur.fetchone()[0]

    def get_unprocessed_entries(self):
        query = "SELECT * FROM unprocessed_entries"
        self.cur.execute(query)
        return self.cur.fetchall()
    def check_table_schema(self, table_name):
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                """)
                columns = cur.fetchall()
                for column in columns:
                    logger.info(f"Column: {column[0]}, Type: {column[1]}, Nullable: {column[2]}")
        except Exception as e:
            logger.error(f"Error checking schema for table {table_name}: {str(e)}")

    def insert_user_and_wallet(self, user_data):
        try:
            with self.conn:
                with self.conn.cursor() as cur:
                    # Insert user
                    user_query = sql.SQL("""
                        INSERT INTO user_accounts (twitter_id, twitter_username)
                        VALUES (%s, %s)
                        ON CONFLICT (twitter_id) DO UPDATE
                        SET twitter_username = EXCLUDED.twitter_username
                        RETURNING twitter_id
                    """)
                    cur.execute(user_query, (user_data['twitter_id'], user_data['twitter_username']))
                    twitter_id = cur.fetchone()[0]

                    # Insert wallet
                    wallet_query = sql.SQL("""
                        INSERT INTO user_wallets (twitter_id, wallet_address, chain, is_primary)
                        VALUES (%s, %s, %s, TRUE)
                        ON CONFLICT (twitter_id, wallet_address) DO NOTHING
                    """)
                    cur.execute(wallet_query, (twitter_id, user_data['wallet_address'], user_data.get('chain', 'solana')))

            logger.info(f"Inserted user {user_data['twitter_username']} with wallet {user_data['wallet_address']}")
            return True
        except Exception as e:
            logger.error(f"Error inserting user and wallet: {str(e)}")
            return False
    def add_wallet_to_user(self, twitter_username, wallet_address, chain='solana'):
        query = sql.SQL("""
            INSERT INTO user_wallets (twitter_id, wallet_address, chain)
            SELECT twitter_id, %s, %s
            FROM user_accounts
            WHERE twitter_username = %s
            ON CONFLICT (twitter_id, wallet_address) DO NOTHING
            RETURNING id
        """)
        with self.conn.cursor() as cur:
            cur.execute(query, (wallet_address, chain, twitter_username))
            result = cur.fetchone()
        self.conn.commit()
        return result is not None

    def archive_user(self, twitter_username):
        query = sql.SQL("""
            UPDATE user_accounts
            SET is_archived = TRUE
            WHERE twitter_username = %s
            RETURNING twitter_id
        """)
        with self.conn.cursor() as cur:
            cur.execute(query, (twitter_username,))
            result = cur.fetchone()
        self.conn.commit()
        return result is not None

    def reactivate_user(self, twitter_username):
        query = sql.SQL("""
            UPDATE user_accounts
            SET is_archived = FALSE
            WHERE twitter_username = %s
            RETURNING twitter_id
        """)
        with self.conn.cursor() as cur:
            cur.execute(query, (twitter_username,))
            result = cur.fetchone()
        self.conn.commit()
        return result is not None

    def archive_wallet(self, twitter_username, wallet_address):
        query = sql.SQL("""
            UPDATE user_wallets
            SET is_archived = TRUE
            WHERE twitter_id = (SELECT twitter_id FROM user_accounts WHERE twitter_username = %s)
            AND wallet_address = %s
            RETURNING id
        """)
        with self.conn.cursor() as cur:
            cur.execute(query, (twitter_username, wallet_address))
            result = cur.fetchone()
        self.conn.commit()
        return result is not None

    def reactivate_wallet(self, twitter_username, wallet_address):
        query = sql.SQL("""
            UPDATE user_wallets
            SET is_archived = FALSE
            WHERE twitter_id = (SELECT twitter_id FROM user_accounts WHERE twitter_username = %s)
            AND wallet_address = %s
            RETURNING id
        """)
        with self.conn.cursor() as cur:
            cur.execute(query, (twitter_username, wallet_address))
            result = cur.fetchone()
        self.conn.commit()
        return result is not None

    def get_user(self, twitter_username):
        query = sql.SQL("""
            SELECT ua.twitter_id, ua.twitter_username, ua.registration_date, ua.is_archived,
                   array_agg(json_build_object('address', uw.wallet_address, 'chain', uw.chain, 'is_archived', uw.is_archived)) as wallets
            FROM user_accounts ua
            LEFT JOIN user_wallets uw ON ua.twitter_id = uw.twitter_id
            WHERE ua.twitter_username = %s
            GROUP BY ua.twitter_id, ua.twitter_username, ua.registration_date, ua.is_archived
        """)
        with self.conn.cursor() as cur:
            cur.execute(query, (twitter_username,))
            return cur.fetchone()

    def get_all_users(self):
        query = sql.SQL("""
            SELECT ua.twitter_id, ua.twitter_username, ua.registration_date, ua.is_archived,
                   array_agg(json_build_object('address', uw.wallet_address, 'chain', uw.chain, 'is_archived', uw.is_archived)) as wallets
            FROM user_accounts ua
            LEFT JOIN user_wallets uw ON ua.twitter_id = uw.twitter_id
            GROUP BY ua.twitter_id, ua.twitter_username, ua.registration_date, ua.is_archived
        """)
        with self.conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

    def update_engagement_score(self, twitter_id, new_score):
        query = sql.SQL("""
            INSERT INTO engagement_scores (twitter_id, score)
            VALUES (%s, %s)
            ON CONFLICT (twitter_id) DO UPDATE
            SET score = EXCLUDED.score, last_updated = CURRENT_TIMESTAMP
        """)
        with self.conn.cursor() as cur:
            cur.execute(query, (twitter_id, new_score))
        self.conn.commit()
        return True
    

    def close(self):
        self.cur.close()
        self.conn.close()