# src/account_management/user_manager.py

import logging
from src.database.sql_db_manager import SQLDBManager
from src.services.twitter_service import TwitterService
from src.services.wallet_validator import WalletValidator

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self):
        self.db_manager = SQLDBManager()
        self.twitter_service = TwitterService()
        self.wallet_validator = WalletValidator()

    def register_user(self, twitter_username, wallet_address, chain='solana'):
        try:
            if self.db_manager.check_username_exists(twitter_username):
                logger.info(f"Account {twitter_username} is already registered.")
                return False, "Duplicate account"

            if not wallet_address:
                logger.info(f"No wallet address provided for {twitter_username}.")
                return False, "Missing wallet address"

            if self.db_manager.check_wallet_exists(wallet_address):
                logger.info(f"Wallet {wallet_address} is already associated with another account.")
                return False, "Duplicate wallet"

            twitter_id = self.twitter_service.get_user_id(twitter_username)
            if not twitter_id:
                logger.info(f"Could not find Twitter ID for username: {twitter_username}")
                return False, "Invalid Twitter username"

            # Insert user and wallet
            self.db_manager.insert_user_and_wallet({
                'twitter_id': twitter_id,
                'twitter_username': twitter_username,
                'wallet_address': wallet_address,
                'chain': chain
            })

            # Add wallet to eligible wallets
            self.wallet_validator.add_eligible_wallet(wallet_address)

            logger.info(f"Successfully registered {twitter_username} with wallet {wallet_address}")
            return True, "Registration successful"
        except Exception as e:
            logger.error(f"Error registering user {twitter_username}: {str(e)}")
            return False, "Registration failed"

    def get_user(self, twitter_username):
        try:
            user = self.db_manager.get_user(twitter_username)
            if not user:
                logger.info(f"User not found: {twitter_username}")
            return user
        except Exception as e:
            logger.error(f"Error retrieving user {twitter_username}: {str(e)}")
            return None

    def add_wallet_to_user(self, twitter_username, wallet_address, chain='solana'):
        try:
            if not self.wallet_validator.validate_address(wallet_address, chain):
                logger.info(f"Invalid wallet address provided for {twitter_username}.")
                return False, "Invalid wallet address"

            if self.db_manager.check_wallet_exists(wallet_address):
                logger.info(f"Wallet {wallet_address} is already associated with another account.")
                return False, "Duplicate wallet"

            success = self.db_manager.add_wallet_to_user(twitter_username, wallet_address, chain)
            if success:
                logger.info(f"Added wallet {wallet_address} to user {twitter_username}")
                return True, "Wallet added successfully"
            else:
                logger.warning(f"Failed to add wallet to user: {twitter_username}")
                return False, "Failed to add wallet"
        except Exception as e:
            logger.error(f"Error adding wallet to user {twitter_username}: {str(e)}")
            return False, "Failed to add wallet"

    def archive_user(self, twitter_username):
        try:
            success = self.db_manager.archive_user(twitter_username)
            if success:
                logger.info(f"Archived user: {twitter_username}")
                return True, "User archived successfully"
            else:
                logger.warning(f"Failed to archive user: {twitter_username}")
                return False, "Failed to archive user"
        except Exception as e:
            logger.error(f"Error archiving user {twitter_username}: {str(e)}")
            return False, "Failed to archive user"

    def reactivate_user(self, twitter_username):
        try:
            success = self.db_manager.reactivate_user(twitter_username)
            if success:
                logger.info(f"Reactivated user: {twitter_username}")
                return True, "User reactivated successfully"
            else:
                logger.warning(f"Failed to reactivate user: {twitter_username}")
                return False, "Failed to reactivate user"
        except Exception as e:
            logger.error(f"Error reactivating user {twitter_username}: {str(e)}")
            return False, "Failed to reactivate user"

    def update_engagement_score(self, twitter_username, new_score):
        try:
            user = self.get_user(twitter_username)
            if not user:
                return False, "User not found"

            success = self.db_manager.update_engagement_score(user['twitter_id'], new_score)
            if success:
                logger.info(f"Updated engagement score for user: {twitter_username}")
                return True, "Engagement score updated successfully"
            else:
                logger.warning(f"Failed to update engagement score for user: {twitter_username}")
                return False, "Failed to update engagement score"
        except Exception as e:
            logger.error(f"Error updating engagement score for user {twitter_username}: {str(e)}")
            return False, "Failed to update engagement score"