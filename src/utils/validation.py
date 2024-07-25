# src/utils/validation.py

from datetime import datetime
from typing import Dict, Any

def validate_tweet_data(tweet_data: Dict[str, Any]) -> bool:
    required_fields = ['id', 'user_id', 'content', 'created_at', 'is_relevant', 'engagement_score']
    
    if not all(field in tweet_data for field in required_fields):
        return False
    
    if not isinstance(tweet_data['id'], str) or not tweet_data['id']:
        return False
    
    if not isinstance(tweet_data['user_id'], str) or not tweet_data['user_id']:
        return False
    
    if not isinstance(tweet_data['content'], str):
        return False
    
    if not isinstance(tweet_data['created_at'], datetime):
        return False
    
    if not isinstance(tweet_data['is_relevant'], bool):
        return False
    
    if not isinstance(tweet_data['engagement_score'], (int, float)) or tweet_data['engagement_score'] < 0:
        return False
    
    return True

def validate_user_data(user_data: Dict[str, Any]) -> bool:
    required_fields = ['id', 'username', 'follower_count', 'created_at']
    
    if not all(field in user_data for field in required_fields):
        return False
    
    if not isinstance(user_data['id'], str) or not user_data['id']:
        return False
    
    if not isinstance(user_data['username'], str) or not user_data['username']:
        return False
    
    if not isinstance(user_data['follower_count'], int) or user_data['follower_count'] < 0:
        return False
    
    if not isinstance(user_data['created_at'], datetime):
        return False
    
    return True

# This file is not meant to be run directly