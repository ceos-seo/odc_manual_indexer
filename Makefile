SHELL:=/bin/bash
docker_compose_dev = docker-compose --project-directory docker/dev -f docker/dev/docker-compose.yml
docker_compose_prod = docker-compose --project-directory docker/prod -f docker/prod/docker-compose.yml

IMG_REPO?=jcrattzama/odc_manual_indexer
IMG_VER?=
ODC_VER?=1.8.3

PROD_OUT_IMG?="${IMG_REPO}:odc${ODC_VER}${IMG_VER}"
DEV_OUT_IMG?="${IMG_REPO}:odc${ODC_VER}${IMG_VER}_dev"

# Production #
up:
	$(docker_compose_prod) up -d --build

up-no-build:
	$(docker_compose_prod) up -d

down: 
	$(docker_compose_prod) down

ssh:
	$(docker_compose_prod) exec manual bash

ps:
	$(docker_compose_prod) ps

restart: down up

restart-no-build: down up-no-build

build-tag: # -e TAG=<tag>
	docker build -f docker/prod/Dockerfile . -t ${PROD_OUT_IMG}

push:
	docker push ${PROD_OUT_IMG}

build-and-push: build-tag push
# End Production #

# Development #
dev-up:
	$(docker_compose_dev) up -d --build

dev-up-no-build:
	$(docker_compose_dev) up -d

dev-down: 
	$(docker_compose_dev) down

dev-ssh:
	$(docker_compose_dev) exec manual bash

dev-ps:
	$(docker_compose_dev) ps

dev-restart: dev-down dev-up

dev-restart-no-build: dev-down dev-up-no-build

dev-build-tag: # -e TAG=<tag>
	docker build -f docker/dev/Dockerfile . -t ${DEV_OUT_IMG}

dev-push:
	docker push ${DEV_OUT_IMG}

build-and-push: build-tag push
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