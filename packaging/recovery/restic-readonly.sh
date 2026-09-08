#!/bin/sh
# The custody bind mount is read-only; forbid commands that mutate repositories.
case "$1" in snapshots|ls|dump|restore) exec /usr/local/bin/restic-real --no-lock "$@" ;; esac
echo 'read-only custody command required' >&2
exit 1
