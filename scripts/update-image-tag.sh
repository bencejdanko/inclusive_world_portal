#!/bin/bash
# update-image-tag.sh - Update image tag in Kustomize manifests
# Usage: ./scripts/update-image-tag.sh [environment] [tag]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Arguments
ENV=${1:-"dev"}
TAG=${2:-"latest"}

# Validate environment
if [[ ! "$ENV" =~ ^(dev|staging|production)$ ]]; then
    echo -e "${RED}Error: Invalid environment. Must be dev, staging, or production${NC}"
    exit 1
fi

OVERLAY_PATH="manifests/overlays/${ENV}"

# Check if overlay exists
if [ ! -d "$OVERLAY_PATH" ]; then
    echo -e "${RED}Error: Overlay directory not found: ${OVERLAY_PATH}${NC}"
    exit 1
fi

echo -e "${GREEN}=== Updating Image Tag ===${NC}"
echo "Environment: ${ENV}"
echo "New Tag: ${TAG}"
echo ""

# Update using kustomize
cd ${OVERLAY_PATH}

if command -v kustomize &> /dev/null; then
    kustomize edit set image \
        your-registry/inclusive-world-portal=your-registry/inclusive-world-portal:${TAG}
    echo -e "${GREEN}✓ Updated with kustomize${NC}"
else
    # Fallback to sed
    sed -i "s|newTag:.*|newTag: ${TAG}|g" kustomization.yaml
    echo -e "${YELLOW}⚠ Updated with sed (kustomize not found)${NC}"
fi

# Show diff
echo ""
echo "Changes:"
git diff kustomization.yaml

# Ask for commit
echo ""
read -p "Commit and push changes? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add kustomization.yaml
    git commit -m "Update ${ENV} image to ${TAG}"
    git push
    echo -e "${GREEN}✓ Changes committed and pushed${NC}"
else
    echo "Changes not committed"
fi
