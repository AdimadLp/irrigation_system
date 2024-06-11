# update_repo.py
import time
import subprocess

def has_repo_changed():
    # Fetch updates from the remote repository
    subprocess.run(["git", "fetch"])
    # Compare the local and remote repositories
    result = subprocess.run(["git", "diff", "HEAD", "origin"], stdout=subprocess.PIPE)
    return len(result.stdout) > 0

def update_repo():
    # Pull updates from the remote repository
    subprocess.run(["git", "pull"])

def check_and_update_repo():
    while True:
        if has_repo_changed():
            update_repo()
        time.sleep(5)  # wait for 5 seconds

if __name__ == "__main__":
    check_and_update_repo()