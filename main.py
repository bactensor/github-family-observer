import subprocess
import time
from init.init_branch_database import init_dataset
from init.init_database import initialize_database
def run_bot(timestamp):
    while True:
        subprocess.run(['python', 'bot/run.py'])  # Replace 'run.py' with the actual filename if different
        time.sleep(timestamp)  # Delay for 5 minutes (300 seconds)

if __name__ == "__main__":
    # init_dataset()
    # initialize_database()
    timestamp = 1000  # Delay in seconds
    run_bot(timestamp)