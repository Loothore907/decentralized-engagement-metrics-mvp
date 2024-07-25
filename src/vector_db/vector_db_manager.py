# src/vector_db/vector_db_manager.py

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import logging
import time
from functools import wraps

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_on_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Vector DB operation failed. Retrying in {delay} seconds. Error: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator

class VectorDBManager:
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = "us-east-1"  # Hardcoded for AWS serverless
        self.index_name = "tweet-embeddings"
        
        if not self.api_key:
            raise ValueError("Pinecone API key not set in .env file")

        logger.info(f"Initializing Pinecone with environment: {self.environment}")
        
        try:
            self.pc = Pinecone(api_key=self.api_key)
            logger.info("Pinecone initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise

        try:
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Successfully connected to Pinecone index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone index: {str(e)}")
            raise

        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded SentenceTransformer model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {e}")
            raise

    def generate_embedding(self, text):
        return self.model.encode(text).tolist()

    @retry_on_error()
    def store_tweet_embedding(self, tweet_id, tweet_text):
        try:
            embedding = self.generate_embedding(tweet_text)
            self.index.upsert(vectors=[(tweet_id, embedding)])
            logger.info(f"Stored embedding for tweet {tweet_id}")
        except Exception as e:
            logger.error(f"Error storing embedding for tweet {tweet_id}: {e}")
            raise

    @retry_on_error()
    def find_similar_tweets(self, query_text, top_k=5):
        try:
            query_embedding = self.generate_embedding(query_text)
            results = self.index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
            logger.info(f"Found {len(results['matches'])} similar tweets")
            return results
        except Exception as e:
            logger.error(f"Error finding similar tweets: {e}")
            raise

    @retry_on_error()
    def batch_store_tweet_embeddings(self, tweets):
        try:
            batch = [(tweet['id'], self.generate_embedding(tweet['text'])) for tweet in tweets]
            self.index.upsert(vectors=batch)
            logger.info(f"Stored embeddings for {len(tweets)} tweets in batch")
        except Exception as e:
            logger.error(f"Error batch storing tweet embeddings: {e}")
            raise

    @retry_on_error()
    def batch_find_similar_tweets(self, query_texts, top_k=5):
        try:
            query_embeddings = [self.generate_embedding(text) for text in query_texts]
            results = self.index.query(vector=query_embeddings, top_k=top_k, include_metadata=True)
            logger.info(f"Found similar tweets for {len(query_texts)} queries")
            return results
        except Exception as e:
            logger.error(f"Error batch finding similar tweets: {e}")
            raise

    def delete_tweet_embedding(self, tweet_id):
        try:
            self.index.delete(ids=[tweet_id])
            logger.info(f"Deleted embedding for tweet {tweet_id}")
        except Exception as e:
            logger.error(f"Error deleting embedding for tweet {tweet_id}: {e}")
            raise

    def get_index_stats(self):
        try:
            stats = self.index.describe_index_stats()
            logger.info(f"Vector DB stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            raise

# Usage example remains the same