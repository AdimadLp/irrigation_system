# update_repo.py
import time
from git import Repo

def has_repo_changed(repo):
    # Fetch updates from the remote repository
    repo.remotes.origin.fetch()
    # Compare the local and remote repositories
    diff = repo.git.diff('HEAD..origin')
    return len(diff) > 0

def update_repo(repo):
    # Pull updates from the remote repository
    repo.remotes.origin.pull()

def check_and_update_repo(repo):
    while True:
        if has_repo_changed(repo):
            update_repo(repo)
        time.sleep(5)  # wait for 5 seconds

if __name__ == "__main__":
    repo = Repo('.')
    check_and_update_repo(repo)