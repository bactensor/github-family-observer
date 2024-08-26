import sqlite3
from github import Github
from config import MAIN_REPO, FORKS, git_access_token
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
def initialize_database_with_branches(repo_data, db_name='db/branch_state1.db'):
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
def print_database_contents(db_name='branch_state.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM branch_state')
    rows = cursor.fetchall()
    
    print("Database contents:")
    for row in rows:
        print(f"Repo: {row[0]}/{row[1]}, Branch: {row[2]}, Commit: {row[3]}")
    
    conn.close()
def init_dataset():
    # Fetch branches and commits from the main repo and specified forks
    repo_data = fetch_github_branches_and_commits(git_access_token, MAIN_REPO, FORKS)
    # Initialize the database with the fetched branch data
    initialize_database_with_branches(repo_data)
    # Uncomment the following line to print the database contents after initialization
    # print_database_contents()
