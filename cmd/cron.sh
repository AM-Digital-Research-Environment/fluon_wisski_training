#!/usr/bin/env sh

set -euo

exec busybox crond -f -L /dev/stdout
