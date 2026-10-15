#!/usr/bin/env bash
# Run only through the serialized CI entrypoint after successful required CI.
set -euo pipefail
umask 077

revision=${1:?Expected the exact tested commit}
[[ $revision =~ ^[a-f0-9]{40}$ ]]
cd /home/devbox/aqllify-app
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=safe.directory
export GIT_CONFIG_VALUE_0=/home/devbox/aqllify-app
[[ $(git rev-parse HEAD) == "$revision" ]]
git diff --quiet
git diff --cached --quiet
compose=(docker compose --profile bot)
"${compose[@]}" config --quiet

backup=/home/devbox/aqllify-backups/"$(date -u +%Y%m%dT%H%M%SZ)-$revision"
mkdir -p "$backup"
cp .env "$backup/environment"
cp docker-compose.yml "$backup/docker-compose.yml"
git ls-tree -r --full-tree "$revision" > "$backup/source-tree.txt"
docker inspect --format '{{.Name}} {{.Image}}' \
    aqllify-backend aqllify-bot aqllify-frontend > "$backup/previous-images.txt"
docker exec aqllify-db pg_dump -U tutor -d tutor_db -Fc > "$backup/database.dump"
test -s "$backup/database.dump"
docker exec -i aqllify-db pg_restore --list < "$backup/database.dump" > "$backup/database-contents.txt"

# Build failures leave the running release untouched. Existing legacy code is
# compatible with additive migration 002 while the new services are prepared.
"${compose[@]}" build --build-arg "RELEASE_REVISION=$revision" backend bot frontend
"${compose[@]}" run --rm --no-deps backend alembic upgrade head
"${compose[@]}" up -d --no-deps --no-build --wait --wait-timeout 120 backend frontend bot

for name in aqllify-backend aqllify-bot aqllify-frontend; do
    image=$(docker inspect --format '{{.Image}}' "$name")
    [[ $(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image") == "$revision" ]]
done
"${compose[@]}" exec -T backend python scripts/check_release.py
curl --noproxy '*' --fail --silent --show-error --max-time 20 \
    --resolve app.aqllify.com:443:127.0.0.1 https://app.aqllify.com/health
printf '\nDelivered %s; backup: %s\n' "$revision" "$backup"
