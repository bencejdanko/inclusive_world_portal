# inclusive_world_portal

A management portal for the Inclusive World team.

### Type checks

Running type checks with mypy:

    uv run mypy inclusive_world_portal

#### Running tests with pytest

    uv run pytest

## Deployment on Google EC2 Instance

Install OS dependencies:

```bash
sudo chmod +x /utility/*

# Install make, Docker, and other build dependencies
sudo utility/install_os_dependencies.sh install
```

Install docker:

```bash
# Add Docker's official GPG key and repository
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to the docker group (so you don't need sudo)
sudo usermod -aG docker $USER

# You'll need to log out and back in for group changes to take effect
# Or run: newgrp docker
```

Install:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env  # or restart your shell
```

Copy paste in env file

```bash
# start service infrastructure
make up 

# install dependencies if not already installed
make install

# make migrations and deploy to database if needed
make makemigrations
make migrate

# run django
make run

# TO HARD RESET:
make reset
make migrate # then you can re migrate
```