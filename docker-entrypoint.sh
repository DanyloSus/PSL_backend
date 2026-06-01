#!/bin/sh
set -e

# Apply pending migrations before serving. Alembic holds a lock on its
# version table, so concurrent instances racing this on deploy is safe.
alembic upgrade head

exec "$@"
