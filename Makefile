PYTHONPATH?=$(PWD)/assimilator
.PHONY: test
test:
	docker stop ass-redis ass-mongodb; docker run --rm -d -p '6379:6379' --name ass-redis redis
	docker run --rm -d -p '27017:27017' --name ass-mongodb mongodb/mongodb-community-server
	uv run examples/simplest_example.py
	echo
	echo '=== simple_events ==='
	uv run examples/simple_events/main.py internal
	uv run examples/simple_events/main.py redis
	echo
	echo "=== simple_database ==="
	uv run examples/simple_database/main.py alchemy
	uv run examples/simple_database/main.py internal
	uv run examples/simple_database/main.py redis
	uv run examples/simple_database/main.py mongo
	echo
	echo "=== complex_database ==="
	uv run examples/complex_database/main.py alchemy
	uv run examples/complex_database/main.py internal
	uv run examples/complex_database/main.py redis
	uv run examples/complex_database/main.py mongo
	echo
	echo "=== fastapi_crud_example ==="
	storage=alchemy uv run examples/fastapi_crud_example/main.py
	storage=internal uv run examples/fastapi_crud_example/main.py
	storage=redis uv run examples/fastapi_crud_example/main.py
	storage=mongo uv run examples/fastapi_crud_example/main.py

	docker stop ass-redis ass-mongodb
