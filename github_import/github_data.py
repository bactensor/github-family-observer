# github_data.py
from github import Github
import config
def get_repo_data():
    access_token = config.git_access_token 
    g = Github(access_token)
    main_repo = g.get_repo(config.MAIN_REPO)
    return main_repo




if __name__ == "__main__":
    get_repo_data()
