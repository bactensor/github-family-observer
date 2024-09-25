# Project Documentation

## Overview

This project is designed to monitor the development progress of a repository by initializing the main repository and its family in a database, and continuously running a specified script at defined intervals. The project consists of several scripts that work together to achieve this goal.

## How to Run the Package

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/bactensor/github-family-observer.git
   cd github-family-observer
   ```

2. **Install Dependencies**:
    ```sh
    pip install -r requirements.txt
   ```

3. **Set Up the .env file**:
    ```sh
    GIT_ACCESS_TOKEN = "your git access token here"
    ```
4. **Prepare the config file**:
The script uses config.yaml file to get the configuration. Each run will store the current state of the repository in a SQLite database. Path to the database is specified in the config file. You can prepare your own config file based on the example in the repository. Here is the structure of the config file:

    ```
    # config.yaml
    DATABASE_DIR: "/path/to/your/db"
    MAIN_REPO: "your main repo owner/name"
    FORKS:
      - "your fork owner/name"
      - "your another fork owner/name"
    DISCORD_WEBHOOK_URL: "your discord bot webhook url here"
    ```

5. **Run the Main Script**:
Run the script providing the config file and (optionally) wait interval between consecutive runs (in seconds).
    ```sh
    python main.py --interval 3600 config.yaml
    ```

## Target
The primary target of this project is to monitor the development progress of a repository by:

* Initializing the main repository and its family in a database.
* Continuously running a specified script to fetch and update the repository state.

## Main Principles

1. Initialization:

 * The main repository and its family are initialized in the database using the GitHub API.
 * The initial state of the repository is fetched and stored in the database.

2. Continuous Monitoring:

 * A specified script is run continuously at defined intervals to update the repository state.
 * The state data is processed to generate reports on branches and pull requests.

## Script Explanations

### `main.py`

This script initializes the main repository and repository family in the database and continuously runs a specified script at defined intervals.

* Functions:
    * run_bot(timestamp): Runs a specified Python script in a loop with a delay between executions.
* Usage:
    * Initializes the database by calling init_main_repo and init_repo_fam.
    * Runs the run.py script continuously with a delay specified by timestamp.

### `database.py`

This script initializes the database with the initial state of the main repository.

* Functions:
    * `init_main_repo()`: Initializes the main repository in the database.
    * `init_repo_fam()`: Initializes the repository family in the database.
    * `fetch_initial_state()`: Fetches the initial state from GitHub.
* Usage:
    * Run this script once to set up the initial state of the database.

* Functions:
    * `branch_report()`: Connects to the database, fetches the state data, and processes it to generate a report.
* Usage:
    * Run this script to generate a report on the current state of branches and pull requests.

## Example Directory Structure

```
project/
    │
    ├── main.py
    │
    ├── observing/
    │   └── bot/bot.py
    │   └── observer/
    │   └── utils/database.py
    │── .env
    ├── db/
    │   └── ob_branch.db
    │   └── ob_prs.db
    │
    │   
    ├── config.yaml
    └── run.py  # Script that is run continuously by main.py
```

## Conclusion

By following this documentation, you should be able to set up and run the project to monitor the development progress of a repository. Each script plays a crucial role in initializing the database, continuously updating the repository state, and generating reports.