# main.py

import asyncio
from src.database.sql_db_manager import SQLDBManager
from src.data_ingestion.twitter_fetcher import TwitterFetcher
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

async def setup():
    db_manager = SQLDBManager()
    await db_manager.initialize()
    twitter_fetcher = TwitterFetcher(db_manager)
    return db_manager, twitter_fetcher

async def cleanup(db_manager):
    await db_manager.close()

async def main():
    db_manager, twitter_fetcher = await setup()
    
    try:
        # Example workflow
        accounts_to_process = ['account1', 'account2', 'account3']  # Replace with actual Twitter IDs
        await twitter_fetcher.process_accounts(accounts_to_process)

        # Fetch and process relevant tweets
        relevant_tweets = await db_manager.get_relevant_tweets(limit=100)
        for tweet in relevant_tweets:
            # Process each relevant tweet (e.g., update engagement metrics)
            pass  # Replace with actual processing logic

        # Add more workflow steps here as needed

    finally:
        await cleanup(db_manager)

if __name__ == "__main__":
    asyncio.run(main())