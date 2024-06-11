#!/bin/bash

function has_repo_changed() {
    # Fetch updates from the remote repository
    git fetch
    # Compare the local and remote repositories
    local result=$(git diff HEAD origin)
    [ -n "$result" ]
}

function update_repo() {
    # Pull updates from the remote repository
    git pull
}

function check_and_update_repo() {
    while true; do
        if has_repo_changed; then
            update_repo
        fi
        sleep 5  # wait for 5 seconds
    done
}

check_and_update_repo