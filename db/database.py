import sqlite3
import json
from github import Github
from config import MAIN_REPO, FORKS, git_access_token
def load_previous_state():
    conn = sqlite3.connect('db/state.db')
    c = conn.cursor()

    # Ensure the table exists
    c.execute('''CREATE TABLE IF NOT EXISTS state (data TEXT)''')

    # Fetch the single item from the table
    c.execute('SELECT data FROM state LIMIT 1')
    row = c.fetchone()
    conn.close()
    # Return the previous state as a dictionary, or initialize if empty
    if row and row[0]:
        try:
            return_cur = row[0]
            return json.loads(return_cur)
        except json.JSONDecodeError:
            print("Error decoding JSON from database. Returning default state.")
            return {"branches": [], "prs": []}
    else:
        return {"branches": [], "prs": []}

def update_database(current_state):
    conn = sqlite3.connect('db/state.db')
    c = conn.cursor()

    # Convert the current state to a JSON string
    json_data = json.dumps(current_state)

    # Clear the existing entry and insert the new state
    c.execute('DELETE FROM state')
    c.execute('INSERT INTO state (data) VALUES (?)', (json_data,))
    conn.commit()
    conn.close()

def fetch_github_branches_and_commits(git_access_token, main_repo, forks):
    g = Github(git_access_token)
    repo_data = {}
    
    # Add main repo and forks to the list
    repo_list = [main_repo] + forks
    
    for repo_info in repo_list:
        owner, name = repo_info.split('/')
        repo = g.get_repo(f"{owner}/{name}")
        
        repo_data[repo_info] = {
            "owner": owner,
            "name": name,
            "branches": {branch.name: branch.commit.sha for branch in repo.get_branches()}
        }
    
    return repo_data
def initialize_database_with_branches(repo_data, db_name='db/branch_state2.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # Drop the table if it exists
    cursor.execute('DROP TABLE IF EXISTS branch_state')
    # Create the table with the updated schema
    cursor.execute('''
        CREATE TABLE branch_state (
            repo_owner TEXT,
            repo_name TEXT,
            branch_name TEXT,
            commit_hash TEXT,
            PRIMARY KEY (repo_owner, repo_name, branch_name)
        )
    ''')
    # Insert the branch data into the table
    for repo_full_name, repo_info in repo_data.items():
        for branch_name, commit_hash in repo_info['branches'].items():
            cursor.execute('''
                INSERT INTO branch_state (repo_owner, repo_name, branch_name, commit_hash)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(repo_owner, repo_name, branch_name) 
                DO UPDATE SET commit_hash=excluded.commit_hash
            ''', (repo_info['owner'], repo_info['name'], branch_name, commit_hash))
    conn.commit()
    conn.close()

def update_database_with_branches():
    repo_data = fetch_github_branches_and_commits(git_access_token, MAIN_REPO, FORKS)
    initialize_database_with_branches(repo_data)
