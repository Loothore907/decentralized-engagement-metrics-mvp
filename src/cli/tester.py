# src/cli/tester.py

import sys
import os
import click

# Add the project root directory to Python's module search path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.account_management.user_manager import UserManager
from src.database.sql_db_manager import SQLDBManager

@click.group()
def cli():
    pass

@cli.command()
@click.option('--username', prompt='Twitter username')
@click.option('--wallet', prompt='Wallet address')
def register_user(username, wallet):
    db_manager = SQLDBManager()
    db_manager.check_table_schema('user_accounts')
    db_manager.check_table_schema('user_wallets')
    
    user_manager = UserManager()
    success, message = user_manager.register_user(username, wallet)
    click.echo(f"Registration {'successful' if success else 'failed'}: {message}")

@cli.command()
@click.option('--username', prompt='Twitter username')
def get_user(username):
    user_manager = UserManager()
    user = user_manager.get_user(username)
    if user:
        click.echo(f"User found: {user}")
    else:
        click.echo("User not found")

if __name__ == '__main__':
    cli()