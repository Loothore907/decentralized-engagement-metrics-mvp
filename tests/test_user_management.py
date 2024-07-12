# tests/test_user_management.py

import unittest
import logging
from unittest.mock import patch, MagicMock
from src.account_management.user_manager import UserManager
from src.services.wallet_validator import WalletValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestUserManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user_manager = UserManager()
        cls.wallet_validator = WalletValidator()
        cls.valid_wallets = list(cls.wallet_validator.eligible_wallets)
        if len(cls.valid_wallets) < 2:
            raise ValueError("Not enough eligible wallets for testing. Ensure at least 2 wallets in eligible_wallets.csv")

    @patch('src.services.twitter_service.TwitterService.get_user_id')
    def test_register_user(self, mock_get_user_id):
        logger.info("Testing user registration")
        mock_get_user_id.return_value = "123456"  # Mocked Twitter ID
        result = self.user_manager.register_user("@testuser", self.valid_wallets[0])
        self.assertTrue(result, "User registration should succeed")

        user = self.user_manager.get_user("@testuser")
        self.assertIsNotNone(user, "User should exist after registration")
        self.assertEqual(user['twitter_username'], "@testuser", "Username should match")
        logger.info("User registration test passed")

    @patch('src.services.twitter_service.TwitterService.get_user_id')
    def test_add_wallet_to_user(self, mock_get_user_id):
        logger.info("Testing adding wallet to user")
        mock_get_user_id.return_value = "234567"  # Mocked Twitter ID
        self.user_manager.register_user("@walletuser", self.valid_wallets[0])
        result = self.user_manager.add_wallet_to_user("@walletuser", self.valid_wallets[1])
        self.assertTrue(result, "Adding wallet should succeed")

        user = self.user_manager.get_user("@walletuser")
        self.assertIn(self.valid_wallets[1], [w['address'] for w in user['wallets']], "New wallet should be added")
        logger.info("Add wallet to user test passed")

    @patch('src.services.twitter_service.TwitterService.get_user_id')
    def test_archive_and_reactivate_user(self, mock_get_user_id):
        logger.info("Testing user archiving and reactivation")
        mock_get_user_id.return_value = "345678"  # Mocked Twitter ID
        self.user_manager.register_user("@archiveuser", self.valid_wallets[0])
        
        archive_result = self.user_manager.archive_user("@archiveuser")
        self.assertTrue(archive_result, "Archiving user should succeed")

        archived_user = self.user_manager.get_user("@archiveuser")
        self.assertTrue(archived_user['is_archived'], "User should be archived")

        reactivate_result = self.user_manager.reactivate_user("@archiveuser")
        self.assertTrue(reactivate_result, "Reactivating user should succeed")

        reactivated_user = self.user_manager.get_user("@archiveuser")
        self.assertFalse(reactivated_user['is_archived'], "User should be reactivated")
        logger.info("User archive and reactivate test passed")

    @patch('src.services.twitter_service.TwitterService.get_user_id')
    def test_invalid_wallet(self, mock_get_user_id):
        logger.info("Testing registration with invalid wallet")
        mock_get_user_id.return_value = "456789"  # Mocked Twitter ID
        result = self.user_manager.register_user("@invaliduser", "invalid_wallet_address")
        self.assertFalse(result, "User registration should fail with invalid wallet")
        logger.info("Invalid wallet test passed")

if __name__ == '__main__':
    unittest.main()