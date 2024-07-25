# File: tests/test_integration.py

import asyncio
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import time

from src.database.sql_db_manager import SQLDBManager
from src.data_ingestion.twitter_fetcher import TwitterFetcher
from src.utils.db_context import get_db

class TestIntegration(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.user_counter = 0

    async def asyncSetUp(self):
        self.db_context = get_db()
        self.db_manager = await self.db_context.__aenter__()
        self.twitter_fetcher = TwitterFetcher(self.db_manager)
        schema_check_result = await self.db_manager.check_schema()
        self.assertTrue(schema_check_result, "Database schema check failed")

    async def asyncTearDown(self):
        if hasattr(self, 'test_user_id'):
            await self.db_manager.execute_query("DELETE FROM user_wallets WHERE twitter_id = $1", self.test_user_id)
            await self.db_manager.execute_query("DELETE FROM user_accounts WHERE twitter_id = $1", self.test_user_id)
        await self.db_context.__aexit__(None, None, None)

    @patch('src.data_ingestion.twitter_fetcher.TwitterFetcher.fetch_user_tweets')
    async def test_user_registration_and_tweet_processing(self, mock_fetch_user_tweets):
        # Generate a unique identifier using timestamp
        unique_id = int(time.time() * 1000)
        self.test_user_id = unique_id
        
        # Test data with unique username and ID
        user_data = {
            'twitter_id': unique_id,  # Already an integer
            'twitter_username': f'test_user_{unique_id}',
            'wallet_address': f'SoLaNaWaLlEtAdDrEsS{unique_id}'
        }
        print(f"Attempting to register user: {user_data['twitter_username']}")

        # Mock tweet data structure
        mock_tweets_data = {
            'data': [{
                'id': str(unique_id + 1),  # Keep as string to mimic Twitter API response
                'text': 'This is a test tweet #DEM',
                'created_at': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                'public_metrics': {
                    'retweet_count': 5,
                    'like_count': 10
                },
                'author_id': str(user_data['twitter_id'])  # Keep as string to mimic Twitter API response
            }],
            'includes': {
                'users': [{
                    'id': str(user_data['twitter_id']),  # Keep as string to mimic Twitter API response
                    'username': user_data['twitter_username'],
                    'created_at': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                }]
            }
        }
        mock_fetch_user_tweets.return_value = mock_tweets_data

        # Test user registration
        result = await self.db_manager.insert_user_and_wallet(user_data)
        print(f"User registration result: {result}")
        self.assertTrue(result, f"User registration failed for {user_data['twitter_username']}")

        # Verify user data
        db_user = await self.db_manager.get_user(user_data['twitter_username'])
        print(f"Retrieved user from database: {db_user}")
        self.assertIsNotNone(db_user, f"Failed to retrieve user {user_data['twitter_username']} from database")
        self.assertEqual(db_user['twitter_username'], user_data['twitter_username'])
        self.assertEqual(int(db_user['twitter_id']), user_data['twitter_id'])  # Convert to int for comparison

        # Test tweet fetching and processing
        await self.twitter_fetcher.process_accounts([str(user_data['twitter_id'])])  # Convert to string for API call

        # Verify tweet data
        db_tweets = await self.db_manager.get_user_tweets(user_data['twitter_id'])
        self.assertEqual(len(db_tweets), 1)
        db_tweet = db_tweets[0]
        self.assertEqual(int(db_tweet['tweet_id']), int(mock_tweets_data['data'][0]['id']))  # Convert both to int for comparison
        self.assertEqual(db_tweet['content'], mock_tweets_data['data'][0]['text'])

        # Verify tweet relevance and engagement score
        self.assertTrue(db_tweet['is_relevant'])
        self.assertEqual(db_tweet['engagement_score'], 15)  # 5 retweets + 10 likes

        # Verify VectorDBManager presence
        self.assertIsNotNone(self.twitter_fetcher.vector_db_manager)

    async def test_database_schema(self):
        schema_check_result = await self.db_manager.check_schema()
        self.assertTrue(schema_check_result, "Database schema check failed")

        # Fetch and print some example Twitter IDs
        twitter_ids = await self.db_manager.fetch_twitter_ids()
        print(f"Example Twitter IDs: {twitter_ids}")

if __name__ == '__main__':
    unittest.main()