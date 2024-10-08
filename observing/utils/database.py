# This script manages the state of GitHub repositories and their branches using SQLite databases.
# It interacts with GitHub to fetch branch and pull request information and stores this data locally.
#
# Functions:
# - fetch_initial_state_main_repo: Fetches branches and pull requests from the main GitHub repository.
# - init_main_repo: Initializes the main repository database with the current state of branches and pull requests.
# - load_previous_main_repo: Loads the previous state of the main repository from the database.
# - update_main_repo: Updates the main repository's state in the database with the current state.
# - fetch_github_branches_and_commits: Retrieves branch names and commit hashes for the main repository and forks.
# - update_database_with_branches: Updates the database with branch information from GitHub.
# - initialize_database_with_branches: Initializes the database with branch data, updating existing entries if needed.
# - init_repo_fam: Initializes the repository family database with branches and commits from GitHub.

import sqlite3
import json
from github import Github
from dotenv import load_dotenv
import os
import ast
load_dotenv()


def fetch_initial_state_main_repo(git_access_token, main_repo_name):

    github_client = Github(git_access_token)
    main_repo = github_client.get_repo(main_repo_name)

    # Fetch branches
    branches = [branch.name for branch in main_repo.get_branches()]

    # Fetch pull requests and create a dictionary with PR title as key and state as value
    prs = {pr.number: pr.state for pr in main_repo.get_pulls(state='all')}

    return {"branches": branches, "prs": prs}

def init_main_repo(db_dir, git_access_token, main_repo_name):

    db_path = os.path.join(db_dir, 'main_repo.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute('DROP TABLE IF EXISTS state')

    c.execute('''CREATE TABLE state (data TEXT)''')

    # Fetch and insert the initial state
    initial_state = fetch_initial_state_main_repo(git_access_token, main_repo_name)
    json_data = json.dumps(initial_state)

    # Insert the JSON data into the table
    c.execute('INSERT INTO state (data) VALUES (?)', (json_data,))

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    
def load_previous_main_repo(db_dir):

    db_path = os.path.join(db_dir, 'main_repo.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS state (data TEXT)''')

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
            return {"branches": [], "prs": {}}
    else:
        return {"branches": [], "prs": {}}

def update_main_repo(db_dir, current_state):

    db_path = os.path.join(db_dir, 'main_repo.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    json_data = json.dumps(current_state)

    # Clear the existing entry and insert the new state
    c.execute('DELETE FROM state')
    c.execute('INSERT INTO state (data) VALUES (?)', (json_data,))
    conn.commit()
    conn.close()

def fetch_github_branches_and_commits(git_access_token, main_repo_name, forks):
    github_client = Github(git_access_token)
    repo_data = {}
    
    # Add main repo and forks to the list
    if isinstance(forks, str):
        forks = ast.literal_eval(forks)
    repo_list = [main_repo_name] + forks
    
    for repo_info in repo_list:
        owner, name = repo_info.split('/')
        repo = github_client.get_repo(f"{owner}/{name}")
        
        repo_data[repo_info] = {
            "owner": owner,
            "name": name,
            "branches": {branch.name: branch.commit.sha for branch in repo.get_branches()}
        }
    
    return repo_data

def update_database_with_branches(db_dir, git_access_token, main_repo_name, forks):
    repo_data = fetch_github_branches_and_commits(git_access_token, main_repo_name, forks)
    initialize_database_with_branches(db_dir, repo_data)

def initialize_database_with_branches(db_dir, repo_data):
    db_path = os.path.join(db_dir, 'repo_fam.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS branch_state')
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
    
def init_repo_fam(db_dir, git_access_token, main_repo_name, forks):
    # Fetch branches and commits from the main repo and specified forks
    repo_data = fetch_github_branches_and_commits(git_access_token, main_repo_name, forks)
    # Initialize the database with the fetched branch data
    initialize_database_with_branches(db_dir, repo_data)