# src/data_ingestion/twitter_fetcher.py

import os
import sys
import asyncio
import aiohttp
from dotenv import load_dotenv
import logging
from typing import List, Dict
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from configs.project_config import PROJECT_ACCOUNTS, KEYWORDS, HASHTAGS
from src.database.sql_db_manager import SQLDBManager
from src.vector_db.vector_db_manager import VectorDBManager

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterFetcher:
    def __init__(self):
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "v2RecentSearchPython"
        }
        self.sql_db_manager = SQLDBManager()
        self.vector_db_manager = VectorDBManager()

    async def fetch_user_tweets(self, user_id: str, max_results: int = 100) -> Dict:
        url = f"{self.base_url}/users/{user_id}/tweets"
        params = {
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,entities,in_reply_to_user_id,referenced_tweets",
            "expansions": "author_id",
            "user.fields": "username,public_metrics,created_at"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"HTTP Error: {response.status}")
                        return None
            except aiohttp.ClientError as e:
                logger.error(f"Network error occurred: {e}")
                return None

    def is_relevant_tweet(self, tweet: Dict) -> bool:
        # Your existing relevance check logic here
        pass

    def process_tweet(self, tweet: Dict, user: Dict):
        is_relevant = self.is_relevant_tweet(tweet)
        
        # Store in SQL database
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'follower_count': user['public_metrics']['followers_count'],
            'created_at': datetime.strptime(user['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
        }
        self.sql_db_manager.insert_user(user_data)
        
        tweet_data = {
            'id': tweet['id'],
            'user_id': user['id'],
            'content': tweet['text'],
            'created_at': datetime.strptime(tweet['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ"),
            'is_relevant': is_relevant,
            'engagement_score': 0  # Placeholder for now
        }
        self.sql_db_manager.insert_tweet(tweet_data)
        
        # Store in vector database
        self.vector_db_manager.store_tweet_embedding(tweet['id'], tweet['text'])

    async def process_accounts(self, account_list: List[str]):
        all_tweets = []
        for account in account_list:
            tweets_data = await self.fetch_user_tweets(account)
            if tweets_data and 'data' in tweets_data:
                user = next((u for u in tweets_data['includes']['users'] if u['id'] == account), None)
                if user:
                    for tweet in tweets_data['data']:
                        self.process_tweet(tweet, user)
                        all_tweets.append(tweet)
        
        # Batch store embeddings
        self.vector_db_manager.batch_store_tweet_embeddings(all_tweets)
        logger.info(f"Processed and stored {len(all_tweets)} tweets")

async def main():
    fetcher = TwitterFetcher()
    
    # Example account list - replace with your actual accounts
    accounts = ["199173175"]  # Your Twitter user ID
    
    await fetcher.process_accounts(accounts)

if __name__ == "__main__":
    asyncio.run(main())