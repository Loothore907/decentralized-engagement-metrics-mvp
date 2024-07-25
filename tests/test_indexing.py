# tests/test_indexing.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.sql_db_manager import SQLDBManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_indexing():
    db_manager = SQLDBManager()
    
    # List of expected indexes
    expected_indexes = [
        ("tweets", "user_id"),
        ("tweets", "created_at"),
        ("tweets", "is_relevant"),
        ("user_accounts", "twitter_username"),
    ]
    
    for table, column in expected_indexes:
        if db_manager.index_exists(table, column):
            logger.info(f"Index on {table}.{column} exists.")
        else:
            logger.warning(f"Index on {table}.{column} does not exist.")

    # Force creation of indexes
    db_manager.check_and_create_indexes()
    
    # Check again after forced creation
    for table, column in expected_indexes:
        if db_manager.index_exists(table, column):
            logger.info(f"Index on {table}.{column} exists after forced creation.")
        else:
            logger.error(f"Failed to create index on {table}.{column}.")

if __name__ == "__main__":
    test_indexing()

# Run command: python -m tests.test_indexing