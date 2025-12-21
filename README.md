# inclusive_world_portal

A management portal for the Inclusive World team.

### Type checks

Running type checks with mypy:

    uv run mypy inclusive_world_portal

#### Running tests with pytest

    uv run pytest

## Deployment

The following details how to deploy this application.

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