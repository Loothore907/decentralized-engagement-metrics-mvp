# src/database/schema_updater.py

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST")
        )
        cur = conn.cursor()

        commands = [
            "DROP TABLE IF EXISTS engagement_scores CASCADE;",
            "DROP TABLE IF EXISTS user_wallets CASCADE;",
            "DROP TABLE IF EXISTS user_accounts CASCADE;",
            """
            CREATE TABLE IF NOT EXISTS user_accounts (
                twitter_id BIGINT PRIMARY KEY,
                twitter_username VARCHAR(255) UNIQUE NOT NULL,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_archived BOOLEAN DEFAULT FALSE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_wallets (
                id SERIAL PRIMARY KEY,
                twitter_id BIGINT REFERENCES user_accounts(twitter_id),
                wallet_address VARCHAR(255) NOT NULL,
                chain VARCHAR(50) DEFAULT 'solana',
                is_primary BOOLEAN DEFAULT FALSE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS engagement_scores (
                twitter_id BIGINT REFERENCES user_accounts(twitter_id),
                score DECIMAL(10,2) DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (twitter_id)
            )
            """
        ]

        for command in commands:
            cur.execute(command)

        # Add unique constraint to wallet_address if it doesn't exist
        cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'unique_wallet_address' AND conrelid = 'user_wallets'::regclass
            ) THEN
                ALTER TABLE user_wallets ADD CONSTRAINT unique_wallet_address UNIQUE (wallet_address);
            END IF;
        END
        $$;
        """)

        conn.commit()
        logger.info("Database schema updated successfully")

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error updating database schema: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    update_schema()