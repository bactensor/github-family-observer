# main.py

from github_import.github_data import get_repo_data
from detecting_changes.discord_report import post_to_discord
from db.database import load_previous_state, update_database, update_database_with_branches
from detecting_changes.pr_report import find_open_merged_pr
from detecting_changes.branch_report import branch_report
import config
from github import Github

def run():
    """
    Main function to orchestrate the process of fetching repository data,
    comparing states, generating reports, and posting them to Discord.
    """
    # Load the previous state from the database
    previous_state = load_previous_state()

    # Fetch current fork branches and main repository data
    main_repo = get_repo_data()

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
    post_to_discord(report_prs, config.DISCORD_WEBHOOK_URL)

    # Generate branch reports
    branches_report, merged_branches_without_pr_report = branch_report()
    post_to_discord(branches_report, config.DISCORD_WEBHOOK_URL)
    post_to_discord(merged_branches_without_pr_report, config.DISCORD_WEBHOOK_URL)
    print("step2 passed")

    # Update the database with the current state
    # update_database(current_state)
    # update_database_with_branches()
    # print("step3 passed")

if __name__ == "__main__":
    run()
