import os
from github import Github
import requests
import json
import sqlite3
import re
import config

# Wraps URLs in angle brackets to prevent Discord from auto-linking them.
def wrap_urls_with_angle_brackets(text):
    url_pattern = r'(https?://\S+)'
    parts = text.split('\n')
    wrapped_parts = [re.sub(url_pattern, r'<\1>', part.strip()) for part in parts]
    return '\n'.join(wrapped_parts)

# Splits a report into chunks that fit within Discord's message limit.
def chunk_report(report):
    DISCORD_MESSAGE_LIMIT = 2000
    report = wrap_urls_with_angle_brackets(report)
    chunks = []
    lines = report.split('\n')
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 > DISCORD_MESSAGE_LIMIT:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += "\n" + line if current_chunk else line

    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

# Initializes the Github API client.
GITHUB_TOKEN = config.git_access_token
g = Github(GITHUB_TOKEN)

# Fetches the current state of repositories (owner, name, branch, commit hash).
def fetch_current_repo_state(repo_family):
    current_state = []
    for repo_full_name in repo_family:
        repo = g.get_repo(repo_full_name)
        branches = repo.get_branches()
        for branch in branches:
            current_state.append({
                "repo_owner": repo.owner.login,
                "repo_name": repo.name,
                "branch_name": branch.name,
                "commit_hash": branch.commit.sha
            })
    return current_state

# Loads the previous state of branches from a SQLite database.
def load_previous_state(db_name='db/branch_state.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT repo_owner, repo_name, branch_name, commit_hash
        FROM branch_state
    ''')
    previous_state = [
        {"repo_owner": row[0], "repo_name": row[1], "branch_name": row[2], "commit_hash": row[3]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return previous_state

# Saves the current state of branches to a JSON file.
def save_current_state(current_state):
    with open("previous_state.json", "w") as f:
        json.dump(current_state, f)

# Converts a list of commit objects to a list of dictionaries with commit details.
def convert_commits(paginated_commits):
    return [{"name": commit.commit.message.split('\n')[0], "link": commit.html_url, "sha": commit.sha} for commit in paginated_commits]

# Compares the current and previous states of branches to identify changes.
def compare_states(current_state, previous_state):
    new_branches = []
    updated_branches = []
    deleted_branches = []
    rebased_branches = []
    current_branch_keys = {(b['repo_owner'], b['repo_name'], b['branch_name']) for b in current_state}
    
    for current_branch in current_state:
        repo_full_name = f"{current_branch['repo_owner']}/{current_branch['repo_name']}"
        repo = g.get_repo(repo_full_name)
        
        previous_branch = next((b for b in previous_state 
                                if b["repo_owner"] == current_branch["repo_owner"] 
                                and b["repo_name"] == current_branch["repo_name"] 
                                and b["branch_name"] == current_branch["branch_name"]), None)
        
        if previous_branch is None:
            default_branch = repo.default_branch
            comparison = repo.compare(default_branch, current_branch["branch_name"])
            if comparison.commits:
                new_branches.append({
                    "repo_owner": current_branch["repo_owner"],
                    "repo_name": current_branch["repo_name"],
                    "branch_name": current_branch["branch_name"],
                    "commit_hash": current_branch["commit_hash"],
                    "commits": convert_commits(comparison.commits)
                })
        elif current_branch["commit_hash"] != previous_branch["commit_hash"]:
            comparison = repo.compare(previous_branch["commit_hash"], current_branch["commit_hash"])
            if comparison.commits:
                updated_branches.append({
                    "repo_owner": current_branch["repo_owner"],
                    "repo_name": current_branch["repo_name"],
                    "branch_name": current_branch["branch_name"],
                    "current_commit_hash": current_branch["commit_hash"],
                    "previous_commit_hash": previous_branch["commit_hash"],
                    "commits": convert_commits(comparison.commits)
                })
                if is_rebased(comparison):
                    rebased_branches.append({
                        "repo_owner": current_branch["repo_owner"],
                        "repo_name": current_branch["repo_name"],
                        "branch_name": current_branch["branch_name"],
                        "commits": convert_commits(comparison.commits)
                    })
    
    for previous_branch in previous_state:
        if (previous_branch['repo_owner'], previous_branch['repo_name'], previous_branch['branch_name']) not in current_branch_keys:
            deleted_branches.append(previous_branch)
    
    return new_branches, updated_branches, deleted_branches, rebased_branches

# Determines if a branch has been rebased by checking the base commit SHA.
def is_rebased(comparison):
    base_commit_sha = comparison.base_commit.sha
    comparison_commit_shas = {commit.sha for commit in comparison.commits}
    
    return base_commit_sha not in comparison_commit_shas

# Finds commits merged into the main branch without an associated pull request.
def find_merged_commits_without_pr(main_repo, current_state, previous_state):
    merged_without_pr = []

    repo = g.get_repo(main_repo)
    main_branch_name = repo.default_branch

    current_main_branch = next((b for b in current_state if b["repo_owner"] == main_repo.split('/')[0] and 
                                b["repo_name"] == main_repo.split('/')[1] and 
                                b["branch_name"] == main_branch_name), None)

    previous_main_branch = next((b for b in previous_state if b["repo_owner"] == main_repo.split('/')[0] and 
                                 b["repo_name"] == main_repo.split('/')[1] and 
                                 b["branch_name"] == main_branch_name), None)

    previous_commit_hash = previous_main_branch["commit_hash"] if previous_main_branch else None
    new_commits = fetch_commits(main_repo, main_branch_name, previous_commit_hash)
    
    pulls = repo.get_pulls(state='closed', base=main_branch_name)

    pr_commit_shas = set()
    for pr in pulls:
        pr_commits = pr.get_commits()
        pr_commit_shas.update(commit.sha for commit in pr_commits)

    for commit in new_commits:
        commit_sha = commit.get("sha")
        if commit_sha and commit_sha not in pr_commit_shas:
            merged_without_pr.append(commit)

    return merged_without_pr

# Fetches commits from a specified branch, optionally since a specific commit.
def fetch_commits(repo_full_name, branch_name, since_commit=None):
    repo = g.get_repo(repo_full_name)
    commits = []
    for commit in repo.get_commits(sha=branch_name):
        if since_commit and commit.sha == since_commit:
            break
        commits.append({
            "name": commit.commit.message.split('\n')[0],
            "link": commit.html_url,
            "sha": commit.sha
        })
    return commits

# Retrieves the GitHub profile image URL for a given repository owner.
def get_github_profile_image(repo_owner):
    url = f"https://api.github.com/users/{repo_owner}"
    response = requests.get(url)
    
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get("avatar_url")
    return None

# Generates a report of branch changes and movements.
def generate_report(new_branches, updated_branches, deleted_branches, rebased_branches):
    fields = []

    if new_branches:
        new_field = {
            "name": "\n\n🌿 **New branches and commits** 🌿\n\n\n",
            "value": "",
            "inline": False
        }
        for branch in new_branches:
            if not branch["commits"]:
                continue
            avatar = get_github_profile_image(branch["repo_owner"])
            repo_full_name = f"{branch['repo_owner']}/{branch['repo_name']}"
            branch_url = f"https://github.com/{repo_full_name}/tree/{branch['branch_name']}"
            new_field["value"] += f"\n* *branch* : [{branch['branch_name']} [{repo_full_name}]]({branch_url})\n"
            for i, commit in enumerate(branch["commits"]):
                new_field["value"] += f"\n * [{commit['name']}]({commit['link']})" if i else f" * [{commit['name']}]({commit['link']})"
        fields.append(new_field)

    if updated_branches:
        updated_field = {
            "name": "\n\n🌿 **Updated branches and commits** 🌿\n",
            "value": "",
            "inline": False
        }
        for branch in updated_branches:
            repo_full_name = f"{branch['repo_owner']}/{branch['repo_name']}"
            branch_url = f"https://github.com/{repo_full_name}/tree/{branch['branch_name']}"
            updated_field["value"] += f"\n* *branch* : [{branch['branch_name']} [{repo_full_name}]]({branch_url})\n"
            for i, commit in enumerate(branch["commits"]):
                updated_field["value"] += f"\n * [{commit['name']}]({commit['link']})" if i else f" * [{commit['name']}]({commit['link']})"
        fields.append(updated_field)

    if deleted_branches:
        deleted_field = {
            "name": "\n\n🌿 **Deleted branches** 🌿\n",
            "value": "",
            "inline": False
        }
        for branch in deleted_branches:
            repo_full_name = f"{branch['repo_owner']}/{branch['repo_name']}"
            branch_url = f"https://github.com/{repo_full_name}/tree/{branch['branch_name']}"
            deleted_field["value"] += f"\n* *branch* : [{branch['branch_name']} [{repo_full_name}]]({branch_url})\n"
        fields.append(deleted_field)

    if rebased_branches:
        rebased_field = {
            "name": "\n\n🌿 **Rebased branches and commits** 🌿\n",
            "value": "",
            "inline": False
        }
        for branch in rebased_branches:
            if not branch["commits"]:
                continue
            repo_full_name = f"{branch['repo_owner']}/{branch['repo_name']}"
            branch_url = f"https://github.com/{repo_full_name}/tree/{branch['branch_name']}"
            rebased_field["value"] += f"\n* *branch* : [{branch['branch_name']} [{repo_full_name}]]({branch_url})\n"
            for i, commit in enumerate(branch["commits"]):
                rebased_field["value"] += f"\n * [{commit['name']}]({commit['link']})" if i else f" * [{commit['name']}]({commit['link']})"
        fields.append(rebased_field)

    embed = {
        "title": "🌟 __ BRANCH REPORT __ 🌟",
        "description": "This is a report of branch movements.",
        "color": 642600,  # Hex color code in decimal
        "fields": fields,
        "thumbnail": {
            "url": "https://example.com/image.png"
        },
    }

    return embed

# Posts the generated report to Discord via a webhook.
# def post_to_discord(embed, webhook_url):
#     data = {
#         "embeds": [embed]
#     }
#     response = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})
#     # print(response.status_code, response.text)

# Updates the SQLite database with the current state of branches.
def update_database(current_state, db_name='branch_state.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS branch_state (
            repo_owner TEXT,
            repo_name TEXT,
            branch_name TEXT,
            commit_hash TEXT,
            PRIMARY KEY (repo_owner, repo_name, branch_name)
        )
    ''')
    
    for branch in current_state:
        cursor.execute('''
            INSERT INTO branch_state (repo_owner, repo_name, branch_name, commit_hash)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(repo_owner, repo_name, branch_name)
            DO UPDATE SET commit_hash=excluded.commit_hash
        ''', (branch['repo_owner'], branch['repo_name'], branch['branch_name'], branch['commit_hash']))
    
    conn.commit()
    conn.close()

# Generates a report for commits merged into the main branch without a pull request.
def generate_merged_commits_without_pr_report(merged_commits_without_pr):
    field = {
        "name": "The following commits were merged into the main branch of __bittensor__ repo without an associated pull request\n\n",
        "value": "",
        "inline": False
    }

    if merged_commits_without_pr:
        for i, commit in enumerate(merged_commits_without_pr):
            field["value"] += f"\n* [{commit['name']}]({commit['link']})" if i else f"* [{commit['name']}]({commit['link']})"
    else:
        field["value"] += "No commits were merged without a pull request.\n"

    embed = {
        "title": "🔥 __ MERGED COMMITS WITHOUT PR __ 🔥",
        "color": 12910592,  # Hex color code in decimal
        "fields": [field],
        "thumbnail": {
            "url": "https://example.com/image.png"
        },
    }

    return embed

# Main function to generate and post branch reports.
def branch_report():
    main_repo = config.MAIN_REPO
    forks = config.FORKS
    webhook = config.DISCORD_WEBHOOK_URL
    repo_family = [main_repo] + forks
    current_state = fetch_current_repo_state(repo_family)
    previous_state = load_previous_state()
    new_branches, updated_branches, deleted_branches, rebased_branches = compare_states(current_state, previous_state)
    merged_without_pr = find_merged_commits_without_pr(main_repo, current_state, previous_state)
    
    merged_commits_without_pr_sha = [commit["sha"] for commit in merged_without_pr]
    rebased_branches_result = [
        cur for cur in rebased_branches
        for commit in cur["commits"]
        if commit["sha"] not in merged_commits_without_pr_sha
    ]

    if new_branches or updated_branches or deleted_branches or rebased_branches:
        report = generate_report(new_branches, updated_branches, deleted_branches, rebased_branches_result)
        # post_to_discord(report, webhook)

    if merged_without_pr:
        merged_commits_without_pr_report = generate_merged_commits_without_pr_report(merged_without_pr)
        # post_to_discord(merged_commits_without_pr_report, webhook)
    return report, merged_commits_without_pr_report
# Uncomment and implement if needed
# def find_rebased_branches(main_repo, current_state, previous_state, merged_without_prs):
