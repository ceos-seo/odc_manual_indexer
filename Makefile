SHELL:=/bin/bash

up:
	docker-compose --project-directory docker \
	-f docker/docker-compose.yml up -d --build

up-no-build:
	docker-compose --project-directory docker \
	-f docker/docker-compose.yml up -d

down: 
	docker-compose --project-directory docker \
	-f docker/docker-compose.yml down

ssh:
	docker-compose --project-directory docker \
	-f docker/docker-compose.yml exec manual bash

ps:
	docker-compose --project-directory docker \
	-f docker/docker-compose.yml ps