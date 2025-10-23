.PHONY: help start stop restart build logs shell install migrate loaddata runserver downloader test clean

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Docker Commands
start: ## Start Docker containers
	docker-compose up -d

stop: ## Stop Docker containers
	docker-compose down

restart: ## Restart Docker containers
	docker-compose restart

build: ## Build Docker containers
	docker-compose build

logs: ## Show Docker logs
	docker-compose logs -f

shell: ## Open shell in Docker container
	docker-compose exec politepol /bin/bash

# Local Development Commands
install: ## Install Python dependencies
	pip install -r requirements.txt

migrate: ## Run Django migrations (local)
	cd frontend && python manage.py migrate

loaddata: ## Load initial data (local)
	cd frontend && python manage.py loaddata fields.json

runserver: ## Run Django development server (local)
	cd frontend && python manage.py runserver

downloader: ## Run downloader server (local)
	python downloader.py

test: ## Run tests
	python test.py

clean: ## Clean Python cache files
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

