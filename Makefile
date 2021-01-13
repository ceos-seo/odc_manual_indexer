SHELL:=/bin/bash
docker_compose_dev = docker-compose --project-directory docker/dev -f docker/dev/docker-compose.yml

# Production #
up:
	docker-compose --project-directory docker/prod \
	-f docker/prod/docker-compose.yml up -d --build

build-tag: # -e TAG=<tag>
	docker build -f docker/prod/Dockerfile . -t ${TAG}

up-no-build:
	docker-compose --project-directory docker/prod \
	-f docker/prod/docker-compose.yml up -d

down: 
	docker-compose --project-directory docker/prod \
	-f docker/prod/docker-compose.yml down

ssh:
	docker-compose --project-directory docker/prod \
	-f docker/prod/docker-compose.yml exec manual bash

ps:
	docker-compose --project-directory docker/prod \
	-f docker/prod/docker-compose.yml ps

restart: down up

restart-no-build: down up-no-build
# End Production #

# Development #
dev-up:
	docker-compose --project-directory docker/dev \
	-f docker/dev/docker-compose.yml up -d --build

dev-build-tag: # -e TAG=<tag>
	docker build -f docker/dev/Dockerfile . -t ${TAG}

dev-up-no-build:
	docker-compose --project-directory docker/dev \
	-f docker/dev/docker-compose.yml up -d

dev-down: 
	docker-compose --project-directory docker/dev \
	-f docker/dev/docker-compose.yml down

dev-ssh:
	docker-compose --project-directory docker/dev \
	-f docker/dev/docker-compose.yml exec manual bash

dev-ps:
	docker-compose --project-directory docker/dev \
	-f docker/dev/docker-compose.yml ps

dev-restart: dev-down dev-up

dev-restart-no-build: dev-down dev-up-no-build
# End Development #

## ODC DB ##

# Create the persistent volume for the ODC database.
create-odc-db-volume:
	docker volume create odc-db-vol

# Delete the persistent volume for the ODC database.
delete-odc-db-volume:
	docker volume rm odc-db-vol

recreate-odc-db-volume: delete-odc-db-volume create-odc-db-volume

# Create the ODC database Docker container.
create-odc-db:
	docker run -d \
	-e POSTGRES_DB=datacube \
	-e POSTGRES_USER=dc_user \
	-e POSTGRES_PASSWORD=localuser1234 \
	--name=odc-db \
	--network="odc" \
	-v odc-db-vol:/var/lib/postgresql/data \
	postgres:10-alpine

start-odc-db:
	docker start odc-db

stop-odc-db:
	docker stop odc-db

restart-odc-db: stop-odc-db start-odc-db

odc-db-ssh:
	docker exec -it odc-db bash

dev-odc-db-init:
	$(docker_compose_dev) exec manual datacube system init

delete-odc-db:
	docker rm odc-db

recreate-odc-db: stop-odc-db delete-odc-db create-odc-db

recreate-odc-db-and-vol: stop-odc-db delete-odc-db recreate-odc-db-volume create-odc-db dev-odc-db-init
## End ODC DB ##