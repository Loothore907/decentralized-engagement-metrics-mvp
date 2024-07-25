# src/data_ingestion/twitter_fetcher.py

import os
import sys
import asyncio
import aiohttp
from dotenv import load_dotenv
import logging
from typing import List, Dict
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from configs.project_config import PROJECT_ACCOUNTS, KEYWORDS, HASHTAGS
from src.database.sql_db_manager import SQLDBManager
from src.vector_db.vector_db_manager import VectorDBManager
from src.utils.validation import validate_tweet_data, validate_user_data
from src.utils.relevance_check import is_tweet_relevant
from src.utils.engagement_score import calculate_engagement_score


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterFetcher:
    def __init__(self, db_manager: SQLDBManager):
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "v2RecentSearchPython"
        }
        self.sql_db_manager = db_manager
        self.vector_db_manager = VectorDBManager()

    async def fetch_user_tweets(self, user_id: str, max_results: int = 100) -> Dict:
        url = f"{self.base_url}/users/{user_id}/tweets"
        params = {
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,entities,in_reply_to_user_id,referenced_tweets",
            "expansions": "author_id",
            "user.fields": "username,public_metrics,created_at"
        }
        
        return await self._make_request(url, params)

    async def fetch_tweets_by_keywords(self, query: str, max_results: int = 100) -> Dict:
        url = f"{self.base_url}/tweets/search/recent"
        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,entities,in_reply_to_user_id,referenced_tweets",
            "expansions": "author_id",
            "user.fields": "username,public_metrics,created_at"
        }
        
        return await self._make_request(url, params)

    async def _make_request(self, url: str, params: Dict) -> Dict:
        async with aiohttp.ClientSession() as session:
            for attempt in range(3):  # Retry up to 3 times
                try:
                    async with session.get(url, headers=self.headers, params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:
                            wait_time = int(response.headers.get('Retry-After', 60))
                            logger.warning(f"Rate limit hit. Waiting for {wait_time} seconds.")
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(f"HTTP Error: {response.status}")
                            return None
                except aiohttp.ClientError as e:
                    logger.error(f"Network error occurred: {e}")
                    await asyncio.sleep(1)
            return None

    def is_relevant_tweet(self, tweet: Dict) -> bool:
        text = tweet['text'].lower()
        if any(keyword.lower() in text for keyword in KEYWORDS + HASHTAGS):
            return True
        if tweet.get('entities', {}).get('mentions'):
            mentioned_users = [mention['username'].lower() for mention in tweet['entities']['mentions']]
            if any(account.lower() in mentioned_users for account in PROJECT_ACCOUNTS):
                return True
        if tweet.get('referenced_tweets'):
            for ref_tweet in tweet['referenced_tweets']:
                if ref_tweet['type'] in ['retweeted', 'quoted'] and ref_tweet['id'] in PROJECT_ACCOUNTS:
                    return True
        return False

    async def process_tweet(self, tweet, user):
        try:
            # Prepare user data
            user_data = {
                'id': user['id'],  # Keep as string
                'username': user['username'],
                'created_at': datetime.strptime(user['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                'follower_count': user.get('public_metrics', {}).get('followers_count', 0)
            }

            # Insert or update user
            user_id = await self.sql_db_manager.insert_or_update_user(user_data)

            if not user_id:
                logger.error(f"Failed to insert or update user: {user_data['username']}")
                return

            # Process tweet
            tweet_data = {
                'id': tweet['id'],  # Keep as string
                'user_id': user_id,  # This is now a string
                'content': tweet['text'],
                'created_at': datetime.strptime(tweet['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                'is_relevant': is_tweet_relevant(tweet['text']),
                'engagement_score': calculate_engagement_score(tweet.get('public_metrics', {}))
            }

            # Insert tweet
            tweet_id = await self.sql_db_manager.insert_tweet(tweet_data)

            if not tweet_id:
                logger.error(f"Failed to insert tweet: {tweet_data['id']}")
                return

            # Log VectorDBManager presence without performing operations
            if self.vector_db_manager:
                logger.info(f"VectorDBManager is available for tweet {tweet_id}")
            else:
                logger.info(f"VectorDBManager is not available for tweet {tweet_id}")

            logger.info(f"Processed tweet {tweet_id} for user {user_data['username']}")

        except Exception as e:
            logger.error(f"Error processing tweet: {str(e)}")

    async def process_accounts(self, account_ids):
        all_tweets = []
        for account_id in account_ids:
            tweets = await self.fetch_user_tweets(str(account_id))  # Ensure account_id is a string for API call
            if tweets and 'data' in tweets and 'includes' in tweets:
                user = tweets['includes']['users'][0]
                for tweet in tweets['data']:
                    await self.process_tweet(tweet, user)
                    all_tweets.append(tweet)
            else:
                logger.warning(f"No tweets found for account ID: {account_id}")

        # Log VectorDBManager presence without performing batch operations
        if self.vector_db_manager:
            logger.info(f"VectorDBManager is available for batch processing of {len(all_tweets)} tweets")
        else:
            logger.info(f"VectorDBManager is not available for batch processing of {len(all_tweets)} tweets")

    async def process_keywords(self, keywords: List[str]):
        query = " OR ".join(keywords)
        tweets_data = await self.fetch_tweets_by_keywords(query)
        
        if tweets_data and 'data' in tweets_data:
            users = {user['id']: user for user in tweets_data['includes']['users']}
            for tweet in tweets_data['data']:
                user = users.get(tweet['author_id'])
                if user:
                    await self.process_tweet(tweet, user)
        
        logger.info(f"Processed tweets for keywords: {keywords}")

# This class is not meant to be run directly