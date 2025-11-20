pypth="$(PWD)/assimilator"
run=PYTHONPATH=$(pypth) uv run --env-file=examples/.env

.PHONY: test
test:
	docker stop ass-redis ass-mongodb; docker run --rm -d -p '6379:6379' --name ass-redis redis
	docker run --rm -d -p '27017:27017' --name ass-mongodb mongodb/mongodb-community-server
	$(run) examples/simplest_example.py
	echo
	echo '=== simple_events ==='
	$(run) examples/simple_events/main.py internal
	$(run) examples/simple_events/main.py redis
	echo
	echo "=== simple_database ==="
	$(run) examples/simple_database/main.py alchemy
	$(run) examples/simple_database/main.py internal
	$(run) examples/simple_database/main.py redis
	$(run) examples/simple_database/main.py mongo
	echo
	echo "=== complex_database ==="
	$(run) examples/complex_database/main.py alchemy
	$(run) examples/complex_database/main.py internal
	$(run) examples/complex_database/main.py redis
	$(run) examples/complex_database/main.py mongo
	echo
	echo "=== fastapi_crud_example ==="
	storage=alchemy $(run) examples/fastapi_crud_example/main.py
	storage=internal $(run) examples/fastapi_crud_example/main.py
	storage=redis $(run) examples/fastapi_crud_example/main.py
	storage=mongo $(run) examples/fastapi_crud_example/main.py

	docker stop ass-redis ass-mongodb

.PHONY: lint
lint:
	uv run ruff check --fix
	uv run ruff format
