# src/account_management/account_processor.py

class AccountProcessor:
    def __init__(self, user_manager, db_manager):
        self.user_manager = user_manager
        self.db_manager = db_manager

    def process_new_entries(self):
        new_entries = self.db_manager.get_unprocessed_entries()
        for entry in new_entries:
            self.process_entry(entry)

    def process_entry(self, entry):
        if self.check_for_duplicates(entry['twitter_username']):
            print(f"Account {entry['twitter_username']} is already associated with another account.")
            return

        if not entry.get('wallet_address'):
            print(f"Wallet address required for {entry['twitter_username']}.")
            return

        result = self.user_manager.register_user(entry['twitter_username'], entry['wallet_address'])
        if result:
            print(f"Successfully registered {entry['twitter_username']}.")
        else:
            print(f"Failed to register {entry['twitter_username']}.")

    def check_for_duplicates(self, twitter_username):
        return self.db_manager.check_username_exists(twitter_username)