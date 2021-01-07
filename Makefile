SHELL:=/bin/bash

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