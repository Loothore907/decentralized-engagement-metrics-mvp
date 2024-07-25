# File: src/utils/relevance_check.py

import json
import os

def load_relevance_criteria():
    """
    Load relevance criteria from tweet_analysis.json file.
    """
    file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'tweet_analysis.json')
    with open(file_path, 'r') as file:
        return json.load(file)

def is_tweet_relevant(tweet_text):
    """
    Check if a tweet is relevant based on criteria from tweet_analysis.json.
    
    NOTE: This is a placeholder implementation. The full logic for relevance checking
    should be implemented here in the future. Currently, it only checks for the presence
    of mentions and returns True if any mention is found.
    """
    criteria = load_relevance_criteria()
    
    # Simple check for mentions (placeholder logic)
    for mention in criteria['mentions']:
        if mention in tweet_text:
            return True
    
    return False

# TODO: Implement more sophisticated relevance checking logic
# This should include checks for keywords, hashtags, and other relevant criteria
# as specified in the tweet_analysis.json file.