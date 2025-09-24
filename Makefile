.PHONY: help dev prod down logs clean test migrate shell db-shell

.DEFAULT_GOAL := help

help:  ## Show this help message.
	@echo "FastAPI Backend Management Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'


dev:  ## Start the development environment.
	docker-compose -f docker-compose.dev.yml up --build

dev-detach:  ## Start the development environment in detached mode.
	docker-compose -f docker-compose.dev.yml up --build -d


prod:  ## Start the production environment.
	docker-compose -f docker-compose.prod.yml up --build -d


down:  ## Stop all running environments (dev and prod).
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.prod.yml down

down-dev: ## Stop the development environment.
	docker-compose -f docker-compose.dev.yml down

down-prod: ## Stop the production environment.
	docker-compose -f docker-compose.prod.yml down


logs:  ## Follow logs for the development environment.
	docker-compose -f docker-compose.dev.yml logs -f

logs-prod:  ## Follow logs for the production environment.
	docker-compose -f docker-compose.prod.yml logs -f


clean:  ## Clean up Docker system (images, volumes, etc.).
	docker system prune -f
	docker volume prune -f

build:  ## Build Docker images for both environments.
	docker-compose -f docker-compose.dev.yml build
	docker-compose -f docker-compose.prod.yml build


test:  ## Run tests in the development environment.
	docker-compose -f docker-compose.dev.yml exec web pytest tests/ -v


migrate:  ## Apply database migrations in the development environment.
	docker-compose -f docker-compose.dev.yml exec web alembic upgrade head

migrate-create:  ## Create a new migration file in the development environment.
	docker-compose -f docker-compose.dev.yml exec web alembic revision --autogenerate -m "$(m)"

stamp:  ## Stamp the database with the latest migration version in the dev environment.
	docker-compose -f docker-compose.dev.yml exec web alembic stamp head


shell:  ## Enter the web container in the development environment.
	docker-compose -f docker-compose.dev.yml exec web bash

db-shell:  ## Enter the database container in the development environment.
	docker-compose -f docker-compose.dev.yml exec db-dev psql -U postgres -d fastapi_db_dev


status:  ## Show container statuses for the development environment.
	docker-compose -f docker-compose.dev.yml ps

status-prod: ## Show container statuses for the production environment.
	docker-compose -f docker-compose.prod.yml ps


req-compile:  ## Compile requirements files.
	pip-compile requirements/base.in -o requirements/base.txt
	pip-compile requirements/dev.in -o requirements/dev.txt
	pip-compile requirements/prod.in -o requirements/prod.txt

req-dev:  ## Install development dependencies.
	pip-sync requirements/dev.txt

req-prod:  ## Install production dependencies.
	pip-sync requirements/prod.txt