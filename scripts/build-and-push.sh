#!/bin/bash
# build-and-push.sh - Script to build and push Docker images
# Usage: ./scripts/build-and-push.sh [registry] [tag]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGISTRY=bencejdanko
TAG=${2:-"$(git rev-parse --short HEAD)"}
IMAGE_NAME="inclusive-world-portal"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo -e "${GREEN}=== Building and Pushing Docker Image ===${NC}"
echo "Registry: ${REGISTRY}"
echo "Image: ${IMAGE_NAME}"
echo "Tag: ${TAG}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: Dockerfile not found. Are you in the project root?${NC}"
    exit 1
fi

# Build the image
echo -e "${YELLOW}Building image...${NC}"
docker build \
    --target production \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --cache-from ${REGISTRY}/${IMAGE_NAME}:latest \
    -t ${FULL_IMAGE} \
    -t ${REGISTRY}/${IMAGE_NAME}:latest \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi

# Show image info
echo ""
echo "Image size:"
docker images ${FULL_IMAGE} --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}"

# Ask for confirmation to push
echo ""
read -p "Push to registry? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Skipping push"
    exit 0
fi

# Push the image
echo -e "${YELLOW}Pushing image...${NC}"
docker push ${FULL_IMAGE}
docker push ${REGISTRY}/${IMAGE_NAME}:latest

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Push successful${NC}"
    echo ""
    echo -e "${GREEN}Image pushed: ${FULL_IMAGE}${NC}"
    echo ""
    echo "To update manifests, run:"
    echo "  cd manifests/overlays/production"
    echo "  kustomize edit set image your-registry/inclusive-world-portal=${FULL_IMAGE}"
else
    echo -e "${RED}✗ Push failed${NC}"
    exit 1
fi
