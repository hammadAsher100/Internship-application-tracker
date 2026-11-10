.PHONY: up down migrate test lint logs
up:
	docker compose up --build -d
down:
	docker compose down
migrate:
	docker compose exec web python manage.py migrate
test:
	docker compose exec web pytest
lint:
	docker compose exec web ruff check .
logs:
	docker compose logs -f web
