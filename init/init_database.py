import sqlite3
from github import Github
import json
import config

def fetch_initial_state():
    # Initialize the GitHub client
    access_token = config.git_access_token
    g = Github(access_token)
    main_repo = g.get_repo("Eros-Rama/bittensor")

    # Fetch branches
    branches = [branch.name for branch in main_repo.get_branches()]

    # Fetch pull requests and create a dictionary with PR title as key and state as value
    prs = {pr.number: pr.state for pr in main_repo.get_pulls(state='all')}

    return {"branches": branches, "prs": prs}

def initialize_database():
    # Connect to the database (or create it if it doesn't exist)
    conn = sqlite3.connect('db/state1.db')
    c = conn.cursor()

    # Drop the table if it exists (useful for development/testing)
    c.execute('DROP TABLE IF EXISTS state')

    # Create the table with the correct schema
    c.execute('''CREATE TABLE state (data TEXT)''')

    # Fetch and insert the initial state
    initial_state = fetch_initial_state()
    # initial_state = {"branches": ["feat/great", "feat-bro", "feat-older", "final", "folder", "master"], "prs": {"4": "open", "3": "closed", "2": "open", "1": "closed"}}
    json_data = json.dumps(initial_state)

    # Insert the JSON data into the table
    c.execute('INSERT INTO state (data) VALUES (?)', (json_data,))

    # Commit changes and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
