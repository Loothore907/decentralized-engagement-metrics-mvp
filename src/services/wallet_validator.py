# src/services/wallet_validator.py

import csv
import os
import logging

logger = logging.getLogger(__name__)

class WalletValidator:
    def __init__(self, eligible_wallets_file='eligible_wallets.csv'):
        self.eligible_wallets = set()
        self.eligible_wallets_file = eligible_wallets_file
        self.load_eligible_wallets()

    def load_eligible_wallets(self):
        try:
            full_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', self.eligible_wallets_file)
            with open(full_path, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    self.eligible_wallets.add(row[0].strip())
            logger.info(f"Loaded {len(self.eligible_wallets)} eligible wallets")
        except Exception as e:
            logger.error(f"Error loading eligible wallets: {str(e)}")

    def validate_address(self, wallet_address, chain='solana'):
        return wallet_address in self.eligible_wallets

    def add_eligible_wallet(self, wallet_address):
        if wallet_address not in self.eligible_wallets:
            self.eligible_wallets.add(wallet_address)
            self._save_eligible_wallets()
            logger.info(f"Added new eligible wallet: {wallet_address}")
        else:
            logger.info(f"Wallet {wallet_address} is already in the eligible list")

    def _save_eligible_wallets(self):
        try:
            full_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', self.eligible_wallets_file)
            with open(full_path, 'w', newline='') as file:
                writer = csv.writer(file)
                for wallet in self.eligible_wallets:
                    writer.writerow([wallet])
            logger.info(f"Saved {len(self.eligible_wallets)} eligible wallets")
        except Exception as e:
            logger.error(f"Error saving eligible wallets: {str(e)}")