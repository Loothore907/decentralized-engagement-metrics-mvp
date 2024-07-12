# src/services/twitter_service.py

import os
import requests
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class TwitterService:
    def __init__(self):
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.base_url = "https://api.twitter.com/2"

    def get_user_id(self, username):
        # Remove '@' symbol if present
        username = username.lstrip('@')
        
        url = f"{self.base_url}/users/by/username/{username}"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            user_data = response.json()
            return user_data['data']['id']
        except requests.RequestException as e:
            logger.error(f"Error fetching Twitter ID for {username}: {str(e)}")
            return None