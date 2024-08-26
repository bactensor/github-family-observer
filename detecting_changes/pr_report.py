from github import Github
import re
import requests
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

def format_report_prs(merged_prs, unmerged_prs, open_prs, repo):
    fields = []

    if merged_prs:
        merged_field = {
            "name": "\n\n🟣 **Merged Pull Requests** 🟣\n\n",
            "value": "",
            "inline": False
        }
        for pr_number in merged_prs:
            pr_details = fetch_pr_details(repo, pr_number)
            # print(pr_details)
            if pr_details:
                merged_field["value"] += f"\n- [{pr_details['title']}]({pr_details['url']}) by [{pr_details['author']}](https://github.com/{pr_details['author']})\n"
                merged_field["value"] += "  Commits:\n"
                for i, commit in enumerate(pr_details["commits"]):
                    if i:
                        merged_field["value"] += f"\n * [{commit['name']}]({commit['link']})"
                    else : 
                        merged_field["value"] += f" * [{commit['name']}]({commit['link']})"
        # merged_field["value"] = add_indentation(merged_field["value"])
        fields.append(merged_field)

    if unmerged_prs:
        unmerged_field = {
            "name": "\n\n🔴 **Closed without merging** 🔴\n\n",
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
                    else : 
                        unmerged_field["value"] += f" * [{commit['name']}]({commit['link']})"
        # unmerged_field["value"] = add_indentation(unmerged_field["value"])
        fields.append(unmerged_field)

    if open_prs:
        open_field = {
            "name": "\n\n🟢 **Opened Pull Requests** 🟢\n\n",
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
                    else : 
                        open_field["value"] += f" * [{commit['name']}]({commit['link']})"
        # open_field["value"] = add_indentation(open_field["value"])
        fields.append(open_field)

    embed = {
        "title": f"🚀 __ PULL REQUEST REPORT __ 🚀",
        "description": "This is a report of pull request activities.",
        "color": 32255,  # Hex color code in decimal
        "fields": fields,
        "thumbnail": {
            "url": "https://example.com/image.png"
        },
        # "footer": {
        #     "text": "This is a footer text"
        # }
    }

    return embed


# def wrap_urls_with_angle_brackets(text):
#     # Regular expression to match URLs
#     url_pattern = r'(https?://\S+)'
    
#     # Split the text by the arrow (:arrow_right:)
#     parts = text.split(':arrow_right:')
#     print(parts)
#     # Wrap URLs in each part
#     wrapped_parts = []
#     for part in parts:
#         wrapped_part = re.sub(url_pattern, r'<\1>', part.strip())
#         wrapped_parts.append(wrapped_part)
    
#     # Join the parts back with the arrow
#     return ' :arrow_right: '.join(wrapped_parts)

# def chanking_report(report):
#     # Discord message limit
#     DISCORD_MESSAGE_LIMIT = 2000

#     # Function to wrap URLs with angle brackets


#     # Wrap URLs in the entire report
#     report = wrap_urls_with_angle_brackets(report)

#     # Split the report into chunks
#     chunks = []
#     lines = report.split('\n')
#     current_chunk = ""

#     for line in lines:
#         # Check if adding the line would exceed the limit
#         if len(current_chunk) + len(line) + 1 > DISCORD_MESSAGE_LIMIT:
#             # If it would, save the current chunk and start a new one
#             chunks.append(current_chunk)
#             current_chunk = line
#         else:
#             # Otherwise, add the line to the current chunk
#             if current_chunk:
#                 current_chunk += "\n" + line
#             else:
#                 current_chunk = line

#     # Don't forget to add the last chunk
#     if current_chunk:
#         chunks.append(current_chunk)
#     return chunks
#     # Send each chunk as a separate message




def find_open_merged_pr(previous_state, current_state, main_repo):
    merged_prs = []
    unmerged_prs = []
    open_prs = []

    # Extract previous and current PR states
    prev_prs = previous_state['prs']
    curr_prs = current_state['prs']
    # print(prev_prs)
    # print(curr_prs)

    # Check for new PRs in the current state
    for pr_number, curr_state in curr_prs.items():
        if pr_number not in prev_prs:
            if curr_state == 'open':
                open_prs.append(pr_number)
            elif curr_state == 'closed':
                # Check if the PR is merged
                pr = main_repo.get_pull(pr_number)
                if pr.merged:  # Replace with actual check for merge status
                    merged_prs.append(pr_number)
                else:
                    unmerged_prs.append(pr_number)

    # Check existing PRs for state changes
    for pr_number, prev_state in prev_prs.items():
        curr_state = curr_prs.get(pr_number)
        
        if curr_state and prev_state == 'open' and curr_state == 'closed':
            # Check if the PR is merged
            pr = main_repo.get_pull(pr_number)
            if pr.merged:  # Replace with actual check for merge status
                merged_prs.append(pr_number)
            else:
                unmerged_prs.append(pr_number)

    # report_merged_prs = format_report_prs(merged_prs, main_repo)
    # report_faild_prs = format_report_prs(unmerged_prs, main_repo)
    # report_open_prs = format_report_prs(open_prs, main_repo)
    report_prs = format_report_prs(merged_prs, unmerged_prs, open_prs, main_repo)



    # print(merged_prs)
    # print(unmerged_prs)
    # print(open_prs)

    # exit(0)
    return report_prs
    

