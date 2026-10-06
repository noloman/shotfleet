#!/bin/sh
# Build the Linux `check` image (Dockerfile) for amd64 and arm64 and push ghcr.io/noloman/shotfleet-check:<version> and :latest.
# One step of each release, run by hand after packaging/publish.sh from the same clean origin/main worktree (packaging/README.md, step 9).
# Needs Docker with buildx and a login with write:packages:  gh auth token | docker login ghcr.io -u noloman --password-stdin
#   PUSH=0 packaging/docker-check.sh   builds both CPUs into the local Docker only (nothing leaves the Mac)
#   TAG=<tag> picks the version tag (default: VERSION in shotfleet.py)
set -eu
cd "$(dirname "$0")/.."
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
TAG=${TAG:-$VERSION}
IMAGE=${IMAGE:-ghcr.io/noloman/shotfleet-check}
[ -z "$(git status --porcelain)" ] || { echo "docker-check: the tree is not clean; build the image from the release commit" >&2; exit 1; }
if [ "${PUSH:-1}" = 1 ]; then out=--push pull=always; else out=--load pull=never; fi
docker buildx build --platform linux/amd64,linux/arm64 --build-arg VERSION="$VERSION" \
  --label org.opencontainers.image.revision="$(git rev-parse HEAD)" -t "$IMAGE:$TAG" -t "$IMAGE:latest" "$out" .
for p in linux/amd64 linux/arm64; do  # what was pushed starts and says its version on both CPUs
  docker run --rm --pull "$pull" --platform "$p" "$IMAGE:$TAG" --version
done
echo "docker-check: $IMAGE:$TAG and :latest ($out)"
