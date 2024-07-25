# File: src/database/sql_db_manager.py

import asyncio
import asyncpg
from dotenv import load_dotenv
import os
import logging
import time
from functools import wraps
# from cachetools import TTLCache, cached
from src.utils.validation import validate_tweet_data, validate_user_data
from functools import lru_cache
from datetime import datetime


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_on_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except asyncpg.exceptions.PostgresError as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Database operation failed. Retrying in {delay} seconds. Error: {e}")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator


def normalize_twitter_id(twitter_id):
    """Convert Twitter ID to an integer format."""
    return int(twitter_id)

class SQLDBManager:
    def __init__(self):
        self.pool = None
#        self.cache = TTLCache(maxsize=100, ttl=300)  # Cache up to 1000 items for 5 minutes



    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            min_size=1,
            max_size=10
        )
        await self.check_and_create_indexes()

    @retry_on_error()
    async def execute_query(self, query, *args, fetch=True):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                start_time = time.time()
                if fetch:
                    result = await conn.fetch(query, *args)
                else:
                    result = await conn.execute(query, *args)
                execution_time = time.time() - start_time
                logger.info(f"Query executed in {execution_time:.2f} seconds")
                return result

    @retry_on_error()
    async def insert_or_update_user(self, user_data):
        query = """
            INSERT INTO user_accounts (twitter_id, twitter_username, registration_date, created_at, follower_count, is_archived)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (twitter_id) DO UPDATE
            SET twitter_username = EXCLUDED.twitter_username,
                created_at = EXCLUDED.created_at,
                follower_count = EXCLUDED.follower_count,
                is_archived = EXCLUDED.is_archived
            RETURNING twitter_id
        """
        result = await self.execute_query(query,
            int(user_data['id']),  # Convert to int here
            user_data['username'],
            user_data.get('registration_date', user_data['created_at']),  # Use created_at as fallback
            user_data['created_at'],
            user_data['follower_count'],
            False  # Default is_archived to False
        )
        return str(result[0]['twitter_id']) if result else None  # Return as string
    
    @retry_on_error()
    async def insert_tweet(self, tweet_data):
        if not validate_tweet_data(tweet_data):
            logger.error(f"Invalid tweet data: {tweet_data}")
            return None

        query = """
            INSERT INTO tweets (id, user_id, content, created_at, is_relevant, engagement_score)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE
            SET content = EXCLUDED.content,
                is_relevant = EXCLUDED.is_relevant,
                engagement_score = EXCLUDED.engagement_score
            RETURNING id
        """
        try:
            result = await self.execute_query(query,
                int(tweet_data['id']),  # Convert to int here
                int(tweet_data['user_id']),  # Convert to int here
                tweet_data['content'],
                tweet_data['created_at'],
                tweet_data['is_relevant'],
                tweet_data['engagement_score']
            )
            return str(result[0]['id']) if result else None  # Return as string
        except Exception as e:
            logger.error(f"Error inserting tweet: {e}")
            return None

    @retry_on_error()
    # @lru_cache(maxsize=100)
    async def get_user_tweets(self, user_id, limit=100):
        query = """
            SELECT id, content, created_at, is_relevant, engagement_score
            FROM tweets
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        return await self.execute_query(query, normalize_twitter_id(user_id), limit)
    
    @retry_on_error()
    # @lru_cache(maxsize=100)
    async def get_relevant_tweets(self, limit=100):
        query = """
            SELECT t.id, t.content, t.created_at, t.engagement_score, u.twitter_username
            FROM tweets t
            JOIN user_accounts u ON t.user_id = u.twitter_id
            WHERE t.is_relevant = TRUE
            ORDER BY t.created_at DESC
            LIMIT $1
        """
        return await self.execute_query(query, limit)
    
    async def check_username_exists(self, twitter_username):
        query = "SELECT EXISTS(SELECT 1 FROM user_accounts WHERE twitter_username = $1)"
        result = await self.execute_query(query, twitter_username)
        return result[0]['exists']

    async def check_wallet_exists(self, wallet_address):
        query = "SELECT EXISTS(SELECT 1 FROM user_wallets WHERE wallet_address = $1)"
        result = await self.execute_query(query, wallet_address)
        return result[0]['exists']

    async def get_unprocessed_entries(self):
        query = "SELECT * FROM unprocessed_entries"
        return await self.execute_query(query)

    async def check_table_schema(self, table_name):
        query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = $1
        """
        columns = await self.execute_query(query, table_name)
        for column in columns:
            logger.info(f"Column: {column['column_name']}, Type: {column['data_type']}, Nullable: {column['is_nullable']}")

    @retry_on_error()
    async def insert_user_and_wallet(self, user_data):
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    
                    
                    user_query = """
                    INSERT INTO user_accounts (twitter_id, twitter_username, registration_date, is_archived)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (twitter_id) DO UPDATE
                    SET twitter_username = EXCLUDED.twitter_username,
                        registration_date = COALESCE(user_accounts.registration_date, EXCLUDED.registration_date),
                        is_archived = EXCLUDED.is_archived
                    RETURNING twitter_id
                    """
                    twitter_id = normalize_twitter_id(user_data['twitter_id'])
                    registration_date = user_data.get('registration_date', datetime.now())
                    is_archived = user_data.get('is_archived', False)
                    twitter_id = await conn.fetchval(user_query, twitter_id, user_data['twitter_username'], registration_date, is_archived)



                    wallet_query = """
                    INSERT INTO user_wallets (twitter_id, wallet_address, is_primary)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (twitter_id) DO UPDATE
                    SET wallet_address = EXCLUDED.wallet_address, is_primary = EXCLUDED.is_primary
                    """
                    await conn.execute(wallet_query, twitter_id, user_data['wallet_address'], user_data.get('is_primary', True))

            logger.info(f"Successfully inserted/updated user and wallet for Twitter ID: {twitter_id}")
            return True
        except ValueError as e:
            logger.error(f"Invalid Twitter ID format: {str(e)}")
            return False
        except asyncpg.exceptions.UniqueViolationError as e:
            logger.error(f"Duplicate entry: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error inserting user and wallet: {str(e)}")
            return False

    async def fetch_twitter_ids(self, limit=5):
        try:
            async with self.pool.acquire() as conn:
                query = "SELECT twitter_username FROM user_accounts LIMIT $1"
                rows = await conn.fetch(query, limit)
                return [row['twitter_username'] for row in rows]
        except Exception as e:
            logging.error(f"Error fetching Twitter IDs: {str(e)}")
            return []

    @retry_on_error()
    async def get_user(self, twitter_username):
        query = """
        SELECT twitter_id, twitter_username, registration_date, is_archived
        FROM user_accounts
        WHERE twitter_username = $1
        """
        result = await self.execute_query(query, twitter_username)
        return result[0] if result else None

    def invalidate_cache(self, key):
        if key in self.cache:
            del self.cache[key]

    async def check_and_create_indexes(self):
        indexes = [
            ("tweets", "user_id"),
            ("tweets", "created_at"),
            ("tweets", "is_relevant"),
            ("user_accounts", "twitter_username"),
        ]
        
        for table, column in indexes:
            if not await self.index_exists(table, column):
                await self.create_index(table, column)

    async def index_exists(self, table, column):
        query = """
        SELECT 1
        FROM pg_indexes
        WHERE tablename = $1 AND indexdef LIKE $2;
        """
        result = await self.execute_query(query, table, f'%{column}%')
        return bool(result)

    async def create_index(self, table, column):
        index_name = f"idx_{table}_{column}"
        query = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column});"
        await self.execute_query(query, fetch=False)
        logger.info(f"Created index {index_name} on {table}.{column}")

    async def check_schema(self):
        try:
            async with self.pool.acquire() as conn:
                # Check user_accounts table
                user_accounts_check = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'user_accounts';
                """)
                
                expected_columns = {
                    'twitter_id': ('bigint', 'NO'),
                    'twitter_username': ('character varying', 'NO'),
                    'created_at': ('timestamp without time zone', 'YES'),
                    'registration_date': ('timestamp without time zone', 'YES'),
                    'is_archived': ('boolean', 'YES'),
                    'follower_count': ('integer', 'YES')
                }

                for col in user_accounts_check:
                    col_name, col_type, is_nullable = col['column_name'], col['data_type'], col['is_nullable']
                    if col_name not in expected_columns:
                        logger.warning(f"Unexpected column in user_accounts table: {col_name}")
                    elif expected_columns[col_name] != (col_type, is_nullable):
                        logger.warning(f"Mismatched column in user_accounts: {col_name}. Expected {expected_columns[col_name]}, got {(col_type, is_nullable)}")

                # Check primary key on user_accounts
                pk_check = await conn.fetchval("""
                    SELECT a.attname
                    FROM   pg_index i
                    JOIN   pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    WHERE  i.indrelid = 'user_accounts'::regclass AND i.indisprimary;
                """)
                if pk_check != 'twitter_id':
                    logger.warning(f"Incorrect primary key on user_accounts table. Expected 'twitter_id', got '{pk_check}'")

                # Check user_wallets table
                user_wallets_check = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'user_wallets';
                """)
                
                expected_wallet_columns = {
                    'twitter_id': ('bigint', 'NO'),
                    'wallet_address': ('character varying', 'NO'),
                    'is_primary': ('boolean', 'NO')
                }

                for col in user_wallets_check:
                    col_name, col_type, is_nullable = col['column_name'], col['data_type'], col['is_nullable']
                    if col_name not in expected_wallet_columns:
                        logger.warning(f"Unexpected column in user_wallets table: {col_name}")
                    elif expected_wallet_columns[col_name] != (col_type, is_nullable):
                        logger.warning(f"Mismatched column in user_wallets: {col_name}. Expected {expected_wallet_columns[col_name]}, got {(col_type, is_nullable)}")

                # Check for unique constraint on user_wallets
                unique_check = await conn.fetchval("""
                    SELECT COUNT(*)
                    FROM information_schema.table_constraints
                    WHERE table_name = 'user_wallets'
                    AND constraint_type = 'UNIQUE'
                    AND constraint_name = 'user_wallets_twitter_id_key';
                """)
                if unique_check == 0:
                    logger.warning("Unique constraint 'user_wallets_twitter_id_key' missing on user_wallets table")

            logger.info("Schema check completed")
            return True
        except Exception as e:
            logger.error(f"Error checking schema: {str(e)}")
            return False    
    async def close(self):
        await self.pool.close()