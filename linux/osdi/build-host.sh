#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p build
stage=$(mktemp -d "$PWD/build/.osdi-stage.XXXXXX")
backup=""
cleanup() {
    if [[ -d "$stage" ]]; then rm -rf "$stage"; fi
    if [[ -n "$backup" && -d "$backup" ]]; then
        if [[ -d build/osdi ]]; then rm -rf "$backup"; else mv "$backup/previous" build/osdi; rmdir "$backup"; fi
    fi
}
trap cleanup EXIT

docker build --pull --no-cache -f osdi/Dockerfile -t ngspice-osdi-builder ..
docker run --rm \
    -e "HOST_UID=$(id -u)" -e "HOST_GID=$(id -g)" \
    -v "$stage:/output" ngspice-osdi-builder \
    python3 /opt/ngspice-osdi/build.py /output

if [[ -d build/osdi ]]; then
    backup=$(mktemp -d "$PWD/build/.osdi-backup.XXXXXX")
    mv build/osdi "$backup/previous"
fi
mv "$stage" build/osdi
if [[ -n "$backup" ]]; then rm -rf "$backup"; backup=""; fi
echo "OSDI bundle: $PWD/build/osdi"
