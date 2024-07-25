# tests/test_validation.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from datetime import datetime
from src.utils.validation import validate_tweet_data, validate_user_data

class TestValidation(unittest.TestCase):
    def test_validate_tweet_data(self):
        valid_tweet = {
            'id': '1234567890',
            'user_id': '9876543210',
            'content': 'This is a test tweet',
            'created_at': datetime.now(),
            'is_relevant': True,
            'engagement_score': 10
        }
        self.assertTrue(validate_tweet_data(valid_tweet))

        # Test missing field
        invalid_tweet = valid_tweet.copy()
        del invalid_tweet['content']
        self.assertFalse(validate_tweet_data(invalid_tweet))

        # Test invalid type
        invalid_tweet = valid_tweet.copy()
        invalid_tweet['engagement_score'] = 'not a number'
        self.assertFalse(validate_tweet_data(invalid_tweet))

        # Test negative engagement score
        invalid_tweet = valid_tweet.copy()
        invalid_tweet['engagement_score'] = -5
        self.assertFalse(validate_tweet_data(invalid_tweet))

    def test_validate_user_data(self):
        valid_user = {
            'id': '9876543210',
            'username': 'testuser',
            'follower_count': 100,
            'created_at': datetime.now()
        }
        self.assertTrue(validate_user_data(valid_user))

        # Test missing field
        invalid_user = valid_user.copy()
        del invalid_user['username']
        self.assertFalse(validate_user_data(invalid_user))

        # Test invalid type
        invalid_user = valid_user.copy()
        invalid_user['follower_count'] = 'not a number'
        self.assertFalse(validate_user_data(invalid_user))

        # Test negative follower count
        invalid_user = valid_user.copy()
        invalid_user['follower_count'] = -10
        self.assertFalse(validate_user_data(invalid_user))

if __name__ == '__main__':
    unittest.main()

# Run command: python -m unittest tests.test_validation