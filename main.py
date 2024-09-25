# This script initializes the main repository and repository family in the database,
# and continuously runs a specified script at defined intervals.
#
# Functions:
# - run_bot: Runs a specified Python script in a loop with a delay between executions.

import subprocess
import time
from observing.utils.database import init_main_repo, init_repo_fam
import os
import argparse
import yaml
import sys
from dotenv import load_dotenv

def create_db_directory(db_path):
    """Creates a db directory at the specified path if it doesn't exist."""
    if not os.path.exists(db_path):
        os.makedirs(db_path)
        print(f"Created directory: {db_path}")
    else:
        print(f"Directory already exists: {db_path}")

def run_bot(timestamp, config_file):
    """Runs the 'run.py' script continuously with a delay specified by timestamp."""
    while True:
        subprocess.run([sys.executable, 'run.py', config_file])   # Pass the config file to run.py
        print(f"run.py finished, sleeping for {timestamp} seconds")
        time.sleep(timestamp)  # Delay for the specified time in seconds

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Initialize and run the bot.")
    parser.add_argument("config_file", help="Path to the YAML configuration file.")
    parser.add_argument("--interval", type=int, default=3600, help="Delay between runs in seconds.")
    args = parser.parse_args()

    load_dotenv()

    # Load configuration from the specified YAML file
    with open(args.config_file, "r") as f:
        config = yaml.safe_load(f)

    start_time = time.time()
    print(f"Initializing started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    git_access_token = os.getenv('GIT_ACCESS_TOKEN')
    db_dir = config.get("DATABASE_DIR")
    main_repo_name = config.get("MAIN_REPO")
    forks = config.get("FORKS", [])

    create_db_directory(db_dir)  # Create a db directory at the specified path

    # Initialize the database with the specified path
    init_main_repo(db_dir, git_access_token, main_repo_name)
    init_repo_fam(db_dir, git_access_token, main_repo_name, forks)

    timestamp = args.interval
    run_bot(timestamp, args.config_file)
