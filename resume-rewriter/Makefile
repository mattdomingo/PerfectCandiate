.PHONY: up down dev logs api-logs fe-logs psql test

up:
	docker compose up -d --build

down:
	docker compose down -v

dev: up
	@echo "Frontend: http://localhost:3000"
	@echo "API:      http://localhost:8000/health"
	@echo "MinIO:    http://localhost:9001 (minioadmin/minioadmin)"

logs:
	docker compose logs -f

api-logs:
	docker compose logs -f api

fe-logs:
	docker compose logs -f frontend

psql:
	docker exec -it rr-postgres psql -U app -d rr

test:
	docker compose exec -T api pytest


