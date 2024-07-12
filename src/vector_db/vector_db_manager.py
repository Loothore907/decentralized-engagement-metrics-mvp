# /home/loothore907/decentralized-engagement-metrics-mvp/src/vector_db/vector_db_manager.py

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDBManager:
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = "us-east-1"  # Hardcoded for AWS serverless
        self.index_name = "tweet-embeddings"
        
        if not self.api_key:
            raise ValueError("Pinecone API key not set in .env file")

        logger.info(f"Initializing Pinecone with environment: {self.environment}")
        
        # Initialize Pinecone
        try:
            self.pc = Pinecone(api_key=self.api_key)
            logger.info("Pinecone initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise

        # Connect to existing Pinecone index
        try:
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Successfully connected to Pinecone index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone index: {str(e)}")
            raise

        # Load the embedding model
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded SentenceTransformer model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {e}")
            raise

    def generate_embedding(self, text):
        return self.model.encode(text).tolist()

    def store_tweet_embedding(self, tweet_id, tweet_text):
        try:
            embedding = self.generate_embedding(tweet_text)
            self.index.upsert(vectors=[(tweet_id, embedding)])
            logger.info(f"Stored embedding for tweet {tweet_id}")
        except Exception as e:
            logger.error(f"Error storing embedding for tweet {tweet_id}: {e}")

    def find_similar_tweets(self, query_text, top_k=5):
        try:
            query_embedding = self.generate_embedding(query_text)
            results = self.index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
            logger.info(f"Found {len(results['matches'])} similar tweets")
            return results
        except Exception as e:
            logger.error(f"Error finding similar tweets: {e}")
            return None

    def batch_store_tweet_embeddings(self, tweets):
        try:
            batch = [(tweet['id'], self.generate_embedding(tweet['text'])) for tweet in tweets]
            self.index.upsert(vectors=batch)
            logger.info(f"Stored embeddings for {len(tweets)} tweets in batch")
        except Exception as e:
            logger.error(f"Error batch storing tweet embeddings: {e}")

# Usage example
if __name__ == "__main__":
    try:
        vector_db = VectorDBManager()
        
        # Store a single tweet
        vector_db.store_tweet_embedding("tweet_id_123", "This is a sample tweet about decentralized finance.")
        
        # Find similar tweets
        similar_tweets = vector_db.find_similar_tweets("What are the benefits of DeFi?")
        print("Similar tweets:", similar_tweets)
        
        # Batch store tweets
        sample_tweets = [
            {"id": "tweet_1", "text": "Exploring the potential of blockchain technology in finance."},
            {"id": "tweet_2", "text": "How smart contracts are revolutionizing traditional banking."}
        ]
        vector_db.batch_store_tweet_embeddings(sample_tweets)
    except Exception as e:
        logger.error(f"An error occurred: {e}")