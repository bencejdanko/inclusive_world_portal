#!/bin/bash
# build-base.sh - Build and push base system image
# Usage: ./scripts/build-base.sh
# Run this: Monthly or when system dependencies change

set -e

REGISTRY=bencejdanko
IMAGE_NAME=inclusive-world-portal-base
TAG=latest

echo "🏗️  Building base system image..."
docker build -f Dockerfile.base -t ${REGISTRY}/${IMAGE_NAME}:${TAG} .

echo "📦 Pushing base system image..."
docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}

echo "✅ Base image built and pushed: ${REGISTRY}/${IMAGE_NAME}:${TAG}"
