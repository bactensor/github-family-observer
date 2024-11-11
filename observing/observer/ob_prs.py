
# This script generates a report on pull request activities in a GitHub repository.
# It identifies open, merged, and closed-without-merging pull requests and formats a report for each category.
#
# Functions:
# - add_indentation: Adds indentation to each line of a given text.
# - fetch_pr_details: Retrieves details of a pull request, including its title, URL, author, and commits.
# - format_report_prs: Formats a report for merged, unmerged, and open pull requests.
# - find_open_merged_pr: Finds open, merged, and unmerged pull requests by comparing previous and current states.


def add_indentation(text, spaces=4):
    indentation = ' ' * spaces
    return '\n'.join([indentation + line for line in text.split('\n')])

def fetch_pr_details(repo, pr_number):
    pr = repo.get_pull(pr_number)
    commits = pr.get_commits()
    commit_details = [{'name': commit.commit.message.split('\n')[0], 'link': commit.html_url} for commit in commits]

    return {
        'title': pr.title,
        'url': pr.html_url,
        'author': pr.user.login,
        'commits': commit_details
    }

def format_report_prs(merged_prs, unmerged_prs, open_prs, reopened_prs, repo):
    fields = []

    if merged_prs:
        merged_field = {
            "name": "\n\n🎉 **Merged Pull Requests** 🎉\n\n",
            "value": "",
            "inline": False
        }
        for pr_number in merged_prs:
            pr_details = fetch_pr_details(repo, pr_number)
            if pr_details:
                merged_field["value"] += f"\n- [{pr_details['title']}]({pr_details['url']}) by [{pr_details['author']}](https://github.com/{pr_details['author']})\n"
                merged_field["value"] += "  Commits:\n"
                for i, commit in enumerate(pr_details["commits"]):
                    if i:
                        merged_field["value"] += f"\n * [{commit['name']}]({commit['link']})"
                    else: 
                        merged_field["value"] += f" * [{commit['name']}]({commit['link']})"
        fields.append(merged_field)

    if unmerged_prs:
        unmerged_field = {
            "name": "\n\n🛑 **Closed without merging** 🛑\n\n",
            "value": "",
            "inline": False
        }
        for pr_number in unmerged_prs:
            pr_details = fetch_pr_details(repo, pr_number)
            if pr_details:
                unmerged_field["value"] += f"\n- [{pr_details['title']}]({pr_details['url']}) by [{pr_details['author']}](https://github.com/{pr_details['author']})\n"
                unmerged_field["value"] += "  Commits:\n"
                for i, commit in enumerate(pr_details["commits"]):
                    if i:
                        unmerged_field["value"] += f"\n * [{commit['name']}]({commit['link']})"
                    else: 
                        unmerged_field["value"] += f" * [{commit['name']}]({commit['link']})"
        fields.append(unmerged_field)

    if reopened_prs:
        reopened_field = {
            "name": "\n\n🚪 **Reopened Pull Requests** 🚪\n\n",
            "value": "",
            "inline": False
        }
        for pr_number in reopened_prs:
            pr_details = fetch_pr_details(repo, pr_number)
            if pr_details:
                reopened_field["value"] += f"\n- [{pr_details['title']}]({pr_details['url']}) by [{pr_details['author']}](https://github.com/{pr_details['author']})\n"
                reopened_field["value"] += "  Commits:\n"
                for i, commit in enumerate(pr_details["commits"]):
                    if i:
                        reopened_field["value"] += f"\n * [{commit['name']}]({commit['link']})"
                    else: 
                        reopened_field["value"] += f" * [{commit['name']}]({commit['link']})"
        fields.append(reopened_field)
    
    if open_prs:
        open_field = {
            "name": "\n\n🌟 **Opened Pull Requests** 🌟\n\n",
            "value": "",
            "inline": False
        }
        for pr_number in open_prs:
            pr_details = fetch_pr_details(repo, pr_number)
            if pr_details:
                open_field["value"] += f"\n- [{pr_details['title']}]({pr_details['url']}) by [{pr_details['author']}](https://github.com/{pr_details['author']})\n"
                open_field["value"] += "  Commits:\n"
                for i, commit in enumerate(pr_details["commits"]):
                    if i:
                        open_field["value"] += f"\n * [{commit['name']}]({commit['link']})"
                    else: 
                        open_field["value"] += f" * [{commit['name']}]({commit['link']})"
        fields.append(open_field)

    embed = {
        "title": "🚀 PULL REQUEST REPORT 🚀",
        "color": 32255,  # Hex color code in decimal
        "fields": fields,
    }
    if not fields:
        embed = None
    return embed

def find_open_merged_pr(previous_state, current_state, main_repo):
    merged_prs = []
    unmerged_prs = []
    open_prs = []
    reopened_prs = []

    # Extract previous and current PR states
    prev_prs = previous_state['prs']
    curr_prs = current_state['prs']

    for pr_number, curr_state in curr_prs.items():
        if pr_number not in prev_prs:
            if curr_state == 'open':
                open_prs.append(pr_number)
            elif curr_state == 'closed':
                # Check if the PR is merged
                pr = main_repo.get_pull(pr_number)
                if pr.merged:
                    merged_prs.append(pr_number)
                else:
                    unmerged_prs.append(pr_number)
        elif prev_prs[pr_number] == 'closed' and curr_state == 'open':
            # PR was reopened
            reopened_prs.append(pr_number)

    # Check existing PRs for state changes
    for pr_number, prev_state in prev_prs.items():
        curr_state = curr_prs.get(pr_number)
        
        if curr_state and prev_state == 'open' and curr_state == 'closed':
            # Check if the PR is merged
            pr = main_repo.get_pull(pr_number)
            if pr.merged:
                merged_prs.append(pr_number)
            else:
                unmerged_prs.append(pr_number)

    report_prs = format_report_prs(merged_prs, unmerged_prs, open_prs, reopened_prs, main_repo)
    return report_prs