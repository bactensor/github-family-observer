
# This script orchestrates the process of monitoring a GitHub repository.
# It fetches repository data, compares current and previous states, generates reports on pull requests and branches,
# and posts these reports to Discord.

from observing.bot.bot import post_to_discord
from observing.utils.database import load_previous_main_repo, update_main_repo, update_database_with_branches
from observing.observer.ob_prs import find_open_merged_pr
from observing.observer.ob_branch import branch_movements
from github import Github
from dotenv import load_dotenv
import os
import time
import argparse
import yaml

def run(config):
    """
    Main function to orchestrate the process of fetching repository data,
    comparing states, generating reports, and posting them to Discord.
    """

    start_time = time.time()
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    load_dotenv()
    db_dir = config.get("DATABASE_DIR")
    
    # Load the previous state from the database
    previous_state = load_previous_main_repo(db_dir)
    
    # Fetch current fork branches and main repository data
    access_token = os.getenv('GIT_ACCESS_TOKEN')
    github_client = Github(access_token)
    main_repo_name = config["MAIN_REPO"]
    main_repo = github_client.get_repo(main_repo_name)
    forks = config.get("FORKS", [])
    discord_webhook_url = config.get("DISCORD_WEBHOOK_URL")

    # Gather pull requests and branches from the main repository
    main_prs = {pr.number: pr.state for pr in main_repo.get_pulls(state="all")}
    main_branches = [branch.name for branch in main_repo.get_branches()]

    # Prepare current state dictionary
    current_state = {
        "branches": main_branches,
        "prs": {int(key): value for key, value in main_prs.items()}
    }
    previous_state["prs"] = {int(key): value for key, value in previous_state["prs"].items()}

    # Find open and merged pull requests
    report_prs = find_open_merged_pr(previous_state, current_state, main_repo)

    print("Merged PR report")
    post_to_discord(report_prs, discord_webhook_url)

    # Generate branch reports
    branches_report, merged_branches_without_pr_report = branch_movements(db_dir, access_token, main_repo_name, forks)
    post_to_discord(branches_report, discord_webhook_url)
    post_to_discord(merged_branches_without_pr_report, discord_webhook_url)
    print("step2 passed")

    # Update the database with the current state
    update_main_repo(db_dir, current_state)
    update_database_with_branches(db_dir, access_token, main_repo_name, forks)
    print("Database update")

    end_time = time.time()
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    print(f"Time consumed: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Monitor a GitHub repository and post updates to Discord."
    )
    parser.add_argument("config_file", help="Path to the YAML configuration file.")
    args = parser.parse_args()

    # Load configuration from the specified YAML file
    with open(args.config_file, "r") as f:
        config = yaml.safe_load(f)

    run(config)