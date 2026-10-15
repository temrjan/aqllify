# Production deployment

Aqllify runs on devbox in `/home/devbox/aqllify-app`. The application Compose project is `aqllify`. Backend and frontend bind only to loopback ports 18000 and 18001. PostgreSQL 17 uses the existing `aqllify_aqllify-db-data` volume. The bot uses the `bot` profile.

The separate Caddy edge serves `app.aqllify.com` and `api.aqllify.com`. It also serves the landing at `aqllify.com` and other applications. Deployment updates only Aqllify backend, frontend and bot. It does not recreate PostgreSQL, the landing or the shared edge.

After both required CI jobs pass on a push to `main`, Actions sends `deploy <tested SHA>` over SSH. Configure repository secrets `SERVER_HOST`, `SERVER_PORT`, `SERVER_USER`, `SSH_KEY` and `SSH_KNOWN_HOSTS` for devbox. Use a dedicated deployment key. Install `ops/ci-entrypoint.sh` as root-owned `/usr/local/sbin/aqllify-ci-entrypoint`, mode 755. Its authorized key must use `restrict,command="/usr/local/sbin/aqllify-ci-entrypoint"`. Pin the server's authenticated SSH host key in `SSH_KNOWN_HOSTS`; do not populate it from an unauthenticated scan during CI.

The entrypoint serializes delivery, rejects tracked local edits and stale commits, fetches `main`, and checks out the tested commit in the existing server checkout. It then runs `ops/deploy.sh`. This creates a private database/configuration backup, builds revision-labelled images, applies the additive migration before replacing application containers, waits for startup, checks running image revisions and runs authenticated read-only curriculum/database/media checks. Failures stop the sequence and fail CI. Backups stay in `/home/devbox/aqllify-backups`; they contain secrets and must never enter Git or a public artifact.

Before the first delivery after a server move, reconcile the known server Compose changes with this version under a saved configuration backup. Preserve `.env`, the database volume and separate Caddy/landing configuration. Set production `LLM_MODEL=gpt-6-luna`, `LLM_REASONING_EFFORT=medium` and `LLM_MAX_COMPLETION_TOKENS=4096`; do not replace the existing bot/API/database credentials.

If build or migration fails, application replacement has not started. A failure during replacement can leave a partial release: inspect the actual containers and schema before recovery. Previous image IDs and the pre-migration dump are retained. Migration 002 is additive; do not downgrade or restore a live database automatically. Recovery that discards newer user data requires a separate decision.

Required release limits still include bilingual editorial/audio approval, real Telegram device testing and live model verification. The read-only release check does not certify those properties. The separate marketing landing is not part of this application release.
