import os
import sys
import asyncio
import aiohttp
from dotenv import load_dotenv
import logging
from typing import List, Dict
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from configs.project_config import PROJECT_ACCOUNTS, KEYWORDS, HASHTAGS
from src.database.db_manager import DBManager

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
        self.db_manager = DBManager()

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
        text = tweet['text'].lower()
        
        if any(account.lower() in text for account in PROJECT_ACCOUNTS):
            return True
        
        if any(keyword.lower() in text for keyword in KEYWORDS):
            return True
        
        tweet_hashtags = [hashtag['tag'].lower() for hashtag in tweet.get('entities', {}).get('hashtags', [])]
        if any(hashtag.lower().lstrip('#') in tweet_hashtags for hashtag in HASHTAGS):
            return True
        
        if tweet.get('in_reply_to_user_id') and any(account.lower() in tweet.get('entities', {}).get('mentions', []) for account in PROJECT_ACCOUNTS):
            return True
        
        return False

    def process_tweet(self, tweet: Dict, user: Dict):
        is_relevant = self.is_relevant_tweet(tweet)
        
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'follower_count': user['public_metrics']['followers_count'],
            'created_at': datetime.strptime(user['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
        }
        self.db_manager.insert_user(user_data)
        
        tweet_data = {
            'id': tweet['id'],
            'user_id': user['id'],
            'content': tweet['text'],
            'created_at': datetime.strptime(tweet['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ"),
            'is_relevant': is_relevant,
            'engagement_score': 0  # You can implement a scoring system later
        }
        self.db_manager.insert_tweet(tweet_data)
        
        metrics_data = {
            'tweet_id': tweet['id'],
            'retweet_count': tweet['public_metrics']['retweet_count'],
            'like_count': tweet['public_metrics']['like_count'],
            'reply_count': tweet['public_metrics']['reply_count'],
            'quote_count': tweet['public_metrics']['quote_count']
        }
        self.db_manager.insert_tweet_metrics(metrics_data)
        
        if is_relevant:
            for project in PROJECT_ACCOUNTS:
                if project.lower() in tweet['text'].lower():
                    mention_data = {
                        'tweet_id': tweet['id'],
                        'project_name': project
                    }
                    self.db_manager.insert_project_mention(mention_data)

    async def process_accounts(self, account_list: List[str]):
        for account in account_list:
            tweets_data = await self.fetch_user_tweets(account)
            if tweets_data and 'data' in tweets_data:
                user = next((u for u in tweets_data['includes']['users'] if u['id'] == account), None)
                if user:
                    for tweet in tweets_data['data']:
                        self.process_tweet(tweet, user)
        
        logger.info("Finished processing accounts")

async def main():
    fetcher = TwitterFetcher()
    
    # Example account list - replace with your actual accounts
    accounts = ["199173175"]  # Your Twitter user ID
    
    await fetcher.process_accounts(accounts)
    fetcher.db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())