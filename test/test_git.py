from github import Github
import config

def get_commits_from_new_branch(new_branch_name):
    g = Github("")
    main_repo = g.get_repo(config.MAIN_REPO)

    # Determine the default branch, typically "main" or "master"
    default_branch = main_repo.default_branch

    print(f"Comparing {new_branch_name} with {default_branch}")

    try:
        # Perform the comparison
        comparison = main_repo.compare(default_branch, new_branch_name)
        new_commits = comparison.commits

        print(f"Successfully fetched) new commits from branch: {new_branch_name}")

        # Create a list with commit messages and URLs
        commit_list = [f"- {commit.commit.message} ({commit.html_url})" for commit in new_commits]

        # Print the formatted commit list
        print("\nCommits:")
        for commit in commit_list:
            print(commit)

    except Exception as e:
        print(f"An error occurred while fetching commits: {e}")

# Call the function with the new branch name
get_commits_from_new_branch("feat-older")
