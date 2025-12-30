# Getting Started (Developers)

> These instructions assume you are using a Linux-based enviroment.
> If you are developing on Windows, please see [WSL](https://learn.microsoft.com/en-us/windows/wsl/about)

## Prerequisites

- [Docker](https://docs.docker.com/engine/install/)
- [uv](https://github.com/astral-sh/uv)
- make

## Instructions to develop locally

1. Clone this repository: 

```bash
git clone https://github.com/bencejdanko/inclusive_world_portal
```

2. Copy `.env.example` to `.env` and make necessary enviroment changes

3. Run the following commands (use `make help` to see more details on each command):

```bash
# start Redis, Minio, Postgres services in the background with docker compose 
# run `make down` to shut down background services
make up

# install necessary OS dependencies
sudo chmod +x /utility/*
sudo utility/install_os_dependencies.sh install

# Install necessary Django packages
make install-dev

# prepare migration scripts for Postgres
make makemigrations

# run migrations
make migrate

# prepare local static files. When adding media and public files, make sure to rerun this.
make collectstatic
```

4. Once the background services are running with Docker, and the migrations have been prepared, you can run the Django service with

```bash
make run


``` 


5. You can also prepare a superuser using `make superuser`.

```bash
make superuser

# then follow instructions
```

The application should be readily accessible at [http://localhost:8002](http://localhost:8002).