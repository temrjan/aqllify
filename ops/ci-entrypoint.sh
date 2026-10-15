#!/usr/bin/env bash
# Install outside the checkout and use as this application's forced SSH command.
set -euo pipefail

cd /home/devbox/aqllify-app
# The existing checkout is owned by devbox; only this root deployment process
# trusts it. Do not change the account's global Git configuration.
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=safe.directory
export GIT_CONFIG_VALUE_0=/home/devbox/aqllify-app
if [[ ${SSH_ORIGINAL_COMMAND:-} == preflight ]]; then
    git rev-parse HEAD
    docker compose --profile bot ps
    exit 0
fi
if [[ ! ${SSH_ORIGINAL_COMMAND:-} =~ ^deploy\ ([a-f0-9]{40})$ ]]; then
    echo 'Only preflight or deploy <40-character commit> is permitted.' >&2
    exit 2
fi
revision=${BASH_REMATCH[1]}
exec 9>/run/lock/aqllify-deploy.lock
flock -n 9 || { echo 'Another Aqllify deployment is running.' >&2; exit 1; }
git diff --quiet
git diff --cached --quiet
git fetch --no-tags origin main
[[ $(git rev-parse FETCH_HEAD) == "$revision" ]] || {
    echo 'Requested revision is no longer the main tip; refusing stale deployment.' >&2
    exit 1
}
git checkout --detach "$revision"
exec bash ops/deploy.sh "$revision"
