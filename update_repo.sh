#!/bin/bash

function has_repo_changed() {
    # Fetch updates from the remote repository
    /usr/bin/git fetch
    # Compare the local and remote repositories
    local result=$(/usr/bin/git diff HEAD origin)
    [ -n "$result" ]
}

function update_repo() {
    # Pull updates from the remote repository
    /usr/bin/git pull
}

function check_and_update_repo() {
    while true; do
        if has_repo_changed; then
            update_repo
        fi
        /bin/sleep 5  # wait for 5 seconds
    done
}

check_and_update_repo