#!/bin/bash

has_repo_changed() {
    # Fetch updates from the remote repository
    /usr/bin/git fetch
    # Compare the local and remote repositories
    local result=$(/usr/bin/git diff HEAD origin)
    [ -n "$result" ]
}

update_repo() {
    # Pull updates from the remote repository
    /usr/bin/git -C reset --hard main
    /usr/bin/git -C pull
}

check_and_update_repo() {
    while true; do
        if has_repo_changed; then
            update_repo
        fi
        /bin/sleep 5  # wait for 5 seconds
    done
}

check_and_update_repo