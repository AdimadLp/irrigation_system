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
      /usr/bin/git pull
}

restart_service() {
    # Restart the service
    /usr/bin/systemctl restart irrigation.service
}

check_and_update_repo() {
    while true; do
        if has_repo_changed; then
            update_repo
            restart_service
        fi
        /bin/sleep 5  # wait for 5 seconds
    done
}

check_and_update_repo