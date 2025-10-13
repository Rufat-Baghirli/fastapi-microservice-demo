.PHONY: help dev dev-detach prod down down-dev down-prod logs logs-prod \
clean build test ci-test migrate migrate-create stamp shell db-shell \
status status-prod req-compile req-dev req-prod restart restart-worker \
logs-worker check-env restart-dev

.DEFAULT_GOAL := help

help:  ## Show this help message.
	@echo "FastAPI Backend Management Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment / Dev / Prod
check-env:  ## Check if .env.dev file exists.
	@if [ ! -f .env.dev ]; then echo ".env.dev not found! Copy .env.dev.example first (cp .env.dev.example .env.dev)."; exit 1; fi
	@echo ".env.dev found."

dev: check-env  ## Start the development environment (foreground).
	docker-compose -f docker-compose.dev.yml up --build

dev-detach: check-env  ## Start the development environment in detached mode.
	docker-compose -f docker-compose.dev.yml up --build -d

dev-restart:  ## Restart the development environment (fast).
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.dev.yml up --build -d

prod:  ## Start the production environment.
	docker-compose -f docker-compose.prod.yml up --build -d

# Stop / Down
down:  ## Stop all running environments (dev and prod).
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.prod.yml down

down-dev: ## Stop the development environment.
	docker-compose -f docker-compose.dev.yml down

down-prod: ## Stop the production environment.
	docker-compose -f docker-compose.prod.yml down

# Logs
logs:  ## Follow logs for the development environment.
	docker-compose -f docker-compose.dev.yml logs -f

logs-prod:  ## Follow logs for the production environment.
	docker-compose -f docker-compose.prod.yml logs -f

logs-worker:  ## Follow logs for the Celery worker (development).
	docker-compose -f docker-compose.dev.yml logs -f worker

# Restart helpers
restart:  ## Restart the entire development environment (down + up).
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.dev.yml up --build -d

restart-worker:  ## Restart only the Celery worker.
	docker-compose -f docker-compose.dev.yml restart worker

# Clean / Build
clean:  ## Clean up Docker system (images, volumes, etc.).
	docker system prune -f
	docker volume prune -f

build:  ## Build Docker images for both environments.
	docker-compose -f docker-compose.dev.yml build
	docker-compose -f docker-compose.prod.yml build

# Tests
test:  ## Run tests in the development environment (interactive).
	docker-compose -f docker-compose.dev.yml exec web python -m pytest tests/ -v

ci-test:  ## Run tests in CI environment (non-interactive, suitable for GitHub Actions).
	docker-compose -f docker-compose.dev.yml run --rm web pytest -q --disable-warnings --maxfail=1

# Migrations
migrate:  ## Apply database migrations in the development environment.
	docker-compose -f docker-compose.dev.yml exec web alembic upgrade head

migrate-create:  ## Create a new migration file in the development environment. Usage: make migrate-create m="message"
	docker-compose -f docker-compose.dev.yml exec web alembic revision --autogenerate -m "$(m)"

stamp:  ## Stamp the database with the latest migration version in the dev environment.
	docker-compose -f docker-compose.dev.yml exec web alembic stamp head

# Shells
shell:  ## Enter the web container in the development environment.
	docker-compose -f docker-compose.dev.yml exec web bash

db-shell:  ## Enter the database container in the development environment.
	docker-compose -f docker-compose.dev.yml exec db-dev psql -U postgres -d fastapi_db_dev

# Status
status:  ## Show container statuses for the development environment.
	docker-compose -f docker-compose.dev.yml ps

status-prod: ## Show container statuses for the production environment.
	docker-compose -f docker-compose.prod.yml ps

# Requirements management
req-compile:  ## Compile requirements files.
	pip-compile requirements/base.in -o requirements/base.txt
	pip-compile requirements/dev.in -o requirements/dev.txt
	pip-compile requirements/prod.in -o requirements/prod.txt

req-dev:  ## Install development dependencies.
	pip-sync requirements/dev.txt

req-prod:  ## Install production dependencies.
	pip-sync requirements/prod.txt
