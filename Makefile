.PHONY: up down migrate seed test lint perf logs
up:
	docker compose up --build -d
down:
	docker compose down
migrate:
	docker compose exec web python manage.py migrate
seed:
	docker compose exec web python manage.py seed_demo
test:
	docker compose exec web pytest
lint:
	docker compose exec web ruff check .
perf:
	docker compose exec web python scripts/perf_check.py
logs:
	docker compose logs -f web
