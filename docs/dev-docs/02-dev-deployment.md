# Deployment Instructions

The application development enviroment is designed to closely mirror how it will be deployed during production:

- Development setup uses Gunicorn
- Development setup runs celery, celerybeat in seperate processes
- Seperate services (Postgres, Redis, Minio) are already assumed to be running asynchronously

For deployment, you can use a similar setup to the [development setup](01-dev-getting-started.md). For process management, we recommend `pm2`, which is node-based.

```bash
# Step 1: Install node
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.nvm/nvm.sh
nvm install --lts
nvm use --lts

# Step 2: Use pm2 to initialize the running server process
pm2 start make --name "make-run" -- run
```