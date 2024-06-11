# update_repo.py
import time
import os

def has_repo_changed():
    # Fetch updates from the remote repository
    os.system("git fetch")
    # Compare the local and remote repositories
    result = os.popen("git diff HEAD origin").read()
    return len(result) > 0

def update_repo():
    # Pull updates from the remote repository
    os.system("git pull")

def check_and_update_repo():
    while True:
        if has_repo_changed():
            update_repo()
        time.sleep(5)  # wait for 5 seconds

if __name__ == "__main__":
    check_and_update_repo()