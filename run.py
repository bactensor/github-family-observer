
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
def run():
    """
    Main function to orchestrate the process of fetching repository data,
    comparing states, generating reports, and posting them to Discord.
    """

    load_dotenv()

    # Load the previous state from the database
    previous_state = load_previous_main_repo()

    # Fetch current fork branches and main repository data
    access_token = os.getenv('GIT_ACCESS_TOKEN')
    g = Github(access_token)
    main_repo = g.get_repo(os.getenv('MAIN_REPO'))
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
    # Gather pull requests and branches from the main repository
    main_prs = {pr.number: pr.state for pr in main_repo.get_pulls(state='all')}
    main_branches = [branch.name for branch in main_repo.get_branches()]

    # Prepare current state dictionary
    current_state = {
        "branches": main_branches,
        "prs": {int(key): value for key, value in main_prs.items()}
    }
    previous_state["prs"] = {int(key): value for key, value in previous_state["prs"].items()}

    # Find open and merged pull requests
    report_prs = find_open_merged_pr(previous_state, current_state, main_repo)
    print("step1 passed")
    # print(report_prs)
    post_to_discord(report_prs, DISCORD_WEBHOOK_URL)

    # Generate branch reports
    branches_report, merged_branches_without_pr_report = branch_movements()
    post_to_discord(branches_report, DISCORD_WEBHOOK_URL)
    post_to_discord(merged_branches_without_pr_report, DISCORD_WEBHOOK_URL)
    print("step2 passed")

    # Update the database with the current state
    update_main_repo(current_state)
    update_database_with_branches()
    print("step3 passed")

if __name__ == "__main__":
    run()
