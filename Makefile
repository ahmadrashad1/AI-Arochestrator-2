.PHONY: dev up down test lint

dev:
	@echo "Start frontend and backend development servers here"

up:
	docker compose up -d

down:
	docker compose down

test:
	@echo "Add backend and frontend test commands here"

lint:
	@echo "Add frontend and backend lint commands here"
