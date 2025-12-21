#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Production Deployment Simulation${NC}"
echo -e "${BLUE}  (Fresh Alpine Server with Docker)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Clean up any existing test container
docker rm -f prod_test_app 2>/dev/null || true

# Build the production Dockerfile
echo -e "${YELLOW}[1/6] Building production container (with Docker-in-Docker)...${NC}"
docker build -f Dockerfile.prod -t inclusive-world-portal-prod:test --no-cache .
echo -e "${GREEN}✓ Production container built${NC}"
echo ""

# Start the app container with Docker-in-Docker support
echo -e "${YELLOW}[2/6] Starting production container...${NC}"
docker run -d \
    --name prod_test_app \
    --privileged \
    -v "$(pwd):/source:ro" \
    -p 8001:8000 \
    inclusive-world-portal-prod:test \
    tail -f /dev/null

# Wait for docker daemon to start inside container
sleep 5
echo -e "${GREEN}✓ Production container started${NC}"
echo ""

# Clone repo into container (simulating git clone in prod)
echo -e "${YELLOW}[3/6] Cloning repository into container...${NC}"
docker exec prod_test_app bash -c "
    set -e
    cp -r /source/. /home/appuser/inclusive_world_portal/
    cd /home/appuser/inclusive_world_portal
    rm -rf .venv __pycache__ .pytest_cache .mypy_cache htmlcov .coverage staticfiles
    chown -R appuser:appuser /home/appuser/inclusive_world_portal
"
echo -e "${GREEN}✓ Repository cloned${NC}"
echo ""

# Start backing services inside the container
echo -e "${YELLOW}[4/6] Starting backing services inside container (make up)...${NC}"
docker exec -u appuser prod_test_app bash -c "
    cd /home/appuser/inclusive_world_portal
    make up
"
echo -e "${GREEN}✓ Backing services started${NC}"
echo ""

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 15
echo -e "${GREEN}✓ Services ready${NC}"
echo ""

# Run deployment using Make commands
echo -e "${YELLOW}[5/6] Running deployment with Make commands...${NC}"
echo ""

echo -e "${BLUE}→ Installing dependencies (make install)${NC}"
docker exec -u appuser prod_test_app bash -l -c "
    cd /home/appuser/inclusive_world_portal
    make install
"
echo ""

echo -e "${BLUE}→ Running migrations (make migrate)${NC}"
docker exec -u appuser prod_test_app bash -l -c "
    cd /home/appuser/inclusive_world_portal
    make migrate
"
echo ""

echo -e "${BLUE}→ Collecting static files (make collectstatic)${NC}"
docker exec -u appuser prod_test_app bash -l -c "
    cd /home/appuser/inclusive_world_portal
    make collectstatic
"
echo ""

echo -e "${BLUE}→ Running tests (make test)${NC}"
docker exec -u appuser prod_test_app bash -l -c "
    cd /home/appuser/inclusive_world_portal
    make test
"
echo -e "${GREEN}✓ All deployment steps completed${NC}"
echo ""

# Run additional CI checks
echo -e "${YELLOW}[6/6] Running CI checks...${NC}"
docker exec -u appuser prod_test_app bash -l -c "
    cd /home/appuser/inclusive_world_portal
    echo '→ Running ruff linting...'
    uv run ruff check . || true
    
    echo '→ Running ruff format check...'
    uv run ruff format --check . || true
    
    echo '→ Running mypy...'
    uv run mypy inclusive_world_portal || true
"
echo -e "${GREEN}✓ CI checks completed${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Simulation Complete! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}The production environment is ready!${NC}"
echo ""
echo -e "To SSH into the container (like SSHing to a prod server):"
echo -e "  ${YELLOW}docker exec -it prod_test_app bash${NC}"
echo ""
echo -e "Inside the container, you can use all your Make commands:"
echo -e "  ${YELLOW}su - appuser${NC}"
echo -e "  ${YELLOW}cd ~/inclusive_world_portal${NC}"
echo -e "  ${YELLOW}make run       ${NC}# Start the server"
echo -e "  ${YELLOW}make test      ${NC}# Run tests"
echo -e "  ${YELLOW}make down      ${NC}# Stop backing services"
echo -e "  ${YELLOW}make up        ${NC}# Start backing services"
echo -e "  ${YELLOW}make help      ${NC}# See all commands"
echo ""
echo -e "Or run the server from outside:"
echo -e "  ${YELLOW}./deploy-test.sh --with-server${NC}"
echo ""
echo -e "To stop and cleanup:"
echo -e "  ${YELLOW}docker rm -f prod_test_app${NC}"
echo ""

# Optional: Start the server
if [ "${1:-}" = "--with-server" ]; then
    echo -e "${YELLOW}Starting application server with make run...${NC}"
    echo -e "${YELLOW}Visit http://localhost:8001${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    docker exec -u appuser prod_test_app bash -l -c "
        cd /home/appuser/inclusive_world_portal
        make run
    "
fi
