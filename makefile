server:
	docker build -t server:latest -f Dockerfile.server .
	docker run -it --name server server:latest
app:
	docker build -t indexer:latest -f Dockerfile.indexer .
	docker run -it --name indexer indexer:latest

clean:
	docker-compose down
	docker-compose build

up:
	docker-compose up

.PHONY: server app clean up