# Training Microservice


[![codecov](https://codecov.io/gh/fiufit-grupo-4/training-microservice/branch/main/graph/badge.svg?token=dcyLtBb60x)](https://codecov.io/gh/fiufit-grupo-4/training-microservice) [![Dev Checks](https://github.com/fiufit-grupo-4/training-microservice/actions/workflows/dev-checks.yml/badge.svg)](https://github.com/fiufit-grupo-4/training-microservice/actions/workflows/dev-checks.yml)

This microservice is in charge of managing the trainings of the users-trainers of the system. It has the basic CRUD of a training with their respective goals. In addition, each training has the functionality to start, pause and complete the training according to the athlete who is performing it. It also implements the basic CRUD of a system of comments and scores for each training.

# Documentation

The link to the API documentation of this microservice can be found in the corresponding Swagger: [API Documentation - Training Microservice](https://training-service-fiufit.herokuapp.com/docs)

# Docker

### Build container:

```$ docker-compose build```

### Start services:

```$ docker-compose up```

### Remove dangling images: 

When you run a ```docker-compose build```, it creates a new image, but it doesn't remove the old one, so you can have a lot of images with the same name but different id. Then, you can remove all of them with the following command:

```$ docker rmi $(docker images -f dangling=true -q) -f```

### Deep Cleaning - Free space on your disk
**Warning**: This will remove all containers, images, volumes and networks not used by at least one container.
Its **recommended** to run this command before ```docker-compose up``` to avoid problems.

```$ docker system prune -a --volumes```

# Dependencies

After any change in *pyproject.toml* file (always execute this before installing):

```$ poetry lock```

### Install Poetry for DEV:

```$ poetry install -E dev```

### Install Poetry for PROD:

```$ poetry install```

# Tests

### Run tests:

```$ poetry run pytest tests```

### Format check:

```$ poetry run flake8 --max-line-length=88 app```

### Auto-format:

```$ poetry run black --skip-string-normalization app```