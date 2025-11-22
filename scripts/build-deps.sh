#!/bin/bash
# build-deps.sh - Build and push dependencies image
# Usage: ./scripts/build-deps.sh
# Run this: When pyproject.toml or uv.lock changes

set -e

REGISTRY=bencejdanko
IMAGE_NAME=inclusive-world-portal-deps
TAG=latest

echo "📚 Building dependencies image..."
DOCKER_BUILDKIT=1 docker build -f Dockerfile.deps -t ${REGISTRY}/${IMAGE_NAME}:${TAG} .

echo "📦 Pushing dependencies image..."
docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}

echo "✅ Dependencies image built and pushed: ${REGISTRY}/${IMAGE_NAME}:${TAG}"
