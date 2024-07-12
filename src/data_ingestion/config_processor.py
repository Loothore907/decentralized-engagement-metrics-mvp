# src/data_ingestion/config_processor.py

import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from configs.project_config import PROJECT_ACCOUNTS, PROJECT_WALLET, USER_ACCOUNTS, KEYWORDS, HASHTAGS
from src.account_management.project_account_manager import ProjectAccountManager
from src.account_management.user_manager import UserManager
from src.database.sql_db_manager import SQLDBManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigProcessor:
    def __init__(self):
        self.project_account_manager = ProjectAccountManager()
        self.user_manager = UserManager()
        self.db_manager = SQLDBManager()

    def process_config(self):
        self.process_project_accounts()
        self.process_project_wallet()
        self.process_user_accounts()
        self.process_keywords_and_hashtags()

    def process_project_accounts(self):
        for account in PROJECT_ACCOUNTS:
            if self.project_account_manager.add_project_account(account):
                logger.info(f"Added project account: {account}")
            else:
                logger.warning(f"Failed to add project account: {account}")

    def process_project_wallet(self):
        if self.project_account_manager.set_project_wallet(PROJECT_WALLET):
            logger.info(f"Set project wallet: {PROJECT_WALLET}")
        else:
            logger.warning(f"Failed to set project wallet: {PROJECT_WALLET}")

    def process_user_accounts(self):
        for account_info in USER_ACCOUNTS:
            twitter_username, wallet_address = account_info.split(',')
            if self.user_manager.register_user(twitter_username, wallet_address):
                logger.info(f"Added user account: {twitter_username} with wallet: {wallet_address}")
            else:
                logger.warning(f"Failed to add user account: {twitter_username}")

    def process_keywords_and_hashtags(self):
        for keyword in KEYWORDS:
            self.db_manager.add_keyword(keyword, is_hashtag=False)
            logger.info(f"Added keyword: {keyword}")

        for hashtag in HASHTAGS:
            self.db_manager.add_keyword(hashtag, is_hashtag=True)
            logger.info(f"Added hashtag: {hashtag}")

def main():
    processor = ConfigProcessor()
    processor.process_config()

if __name__ == "__main__":
    main()