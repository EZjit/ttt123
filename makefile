export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
# export DOCKER_DEFAULT_PLATFORM=linux/amd64

format:
	uv run ruff format .
	uv run ruff check . --fix

check:
	uv run ruff format . --check
	uv run ruff check .

build:
	docker compose build

up:
	docker compose up

down:
	docker compose down

drop:
	docker compose down -v

migrate:
	docker compose run --rm web uv run alembic upgrade head

pre_commit_install:
	uv run --all-extras pre-commit install

pre_commit_run:
	uv run --all-extras pre-commit run --all-files

pre_commit_autoupdate:
	uv run --all-extras pre-commit autoupdate

bash:
	docker compose run --rm web bash

test:
	docker compose run --rm web uv run pytest ./tests

pre_commit_install:
	uv run pre-commit install

pre_commit_run:
	uv run --all-extras pre-commit run --all-files