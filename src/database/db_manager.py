import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST")
            )
            self.cur = self.conn.cursor()
            logger.info("Successfully connected to the database")
        except Exception as e:
            logger.error(f"Error connecting to the database: {e}")
            raise

    def insert_user(self, user_data):
        try:
            self.cur.execute(
                sql.SQL("INSERT INTO users (id, username, follower_count, created_at) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET follower_count = EXCLUDED.follower_count"),
                (user_data['id'], user_data['username'], user_data['follower_count'], user_data['created_at'])
            )
            self.conn.commit()
            logger.info(f"User {user_data['username']} inserted/updated successfully")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting user: {e}")

    def insert_tweet(self, tweet_data):
        try:
            self.cur.execute(
                sql.SQL("INSERT INTO tweets (id, user_id, content, created_at, is_relevant, engagement_score) VALUES (%s, %s, %s, %s, %s, %s)"),
                (tweet_data['id'], tweet_data['user_id'], tweet_data['content'], tweet_data['created_at'], tweet_data['is_relevant'], tweet_data['engagement_score'])
            )
            self.conn.commit()
            logger.info(f"Tweet {tweet_data['id']} inserted successfully")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting tweet: {e}")

    def insert_tweet_metrics(self, metrics_data):
        try:
            self.cur.execute(
                sql.SQL("INSERT INTO tweet_metrics (tweet_id, retweet_count, like_count, reply_count, quote_count) VALUES (%s, %s, %s, %s, %s)"),
                (metrics_data['tweet_id'], metrics_data['retweet_count'], metrics_data['like_count'], metrics_data['reply_count'], metrics_data['quote_count'])
            )
            self.conn.commit()
            logger.info(f"Metrics for tweet {metrics_data['tweet_id']} inserted successfully")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting tweet metrics: {e}")

    def insert_project_mention(self, mention_data):
        try:
            self.cur.execute(
                sql.SQL("INSERT INTO project_mentions (tweet_id, project_name) VALUES (%s, %s)"),
                (mention_data['tweet_id'], mention_data['project_name'])
            )
            self.conn.commit()
            logger.info(f"Project mention for tweet {mention_data['tweet_id']} inserted successfully")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting project mention: {e}")

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")

# Example usage
if __name__ == "__main__":
    db = DBManager()
    try:
        # Test inserting a user
        db.insert_user({
            'id': 123456,
            'username': 'test_user',
            'follower_count': 1000,
            'created_at': '2024-07-04 12:00:00'
        })
        
        # Test inserting a tweet
        db.insert_tweet({
            'id': 789012,
            'user_id': 123456,
            'content': 'This is a test tweet',
            'created_at': '2024-07-04 12:05:00',
            'is_relevant': True,
            'engagement_score': 0.75
        })
        
        # Test inserting tweet metrics
        db.insert_tweet_metrics({
            'tweet_id': 789012,
            'retweet_count': 5,
            'like_count': 10,
            'reply_count': 2,
            'quote_count': 1
        })
        
        # Test inserting a project mention
        db.insert_project_mention({
            'tweet_id': 789012,
            'project_name': 'TestProject'
        })
    
    finally:
        db.close()