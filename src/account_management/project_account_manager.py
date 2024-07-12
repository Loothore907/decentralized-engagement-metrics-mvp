# src/account_management/project_account_manager.py

import logging
from src.database.sql_db_manager import SQLDBManager
from src.services.twitter_service import TwitterService

logger = logging.getLogger(__name__)

class ProjectAccountManager:
    def __init__(self):
        self.db_manager = SQLDBManager()
        self.twitter_service = TwitterService()

    def add_project_account(self, twitter_username):
        try:
            twitter_id = self.get_twitter_id(twitter_username)  # Implement this method
            self.db_manager.insert_project_account(twitter_id, twitter_username)
            return True
        except Exception as e:
            logger.error(f"Error adding project account {twitter_username}: {str(e)}")
            return False
    def set_project_wallet(self, wallet_address):
        try:
            self.db_manager.set_project_wallet(wallet_address)
            return True
        except Exception as e:
            logger.error(f"Error setting project wallet {wallet_address}: {str(e)}")
            return False        
    def get_all_project_accounts(self):
        return self.db_manager.get_all_project_accounts()

    def archive_project_account(self, twitter_username):
            try:
                self.db_manager.archive_project_account(twitter_username)
                logger.info(f"Archived project account: {twitter_username}")
                return True
            except Exception as e:
                logger.error(f"Error archiving project account {twitter_username}: {str(e)}")
                return False

    def get_archived_project_accounts(self):
        return self.db_manager.get_archived_project_accounts()