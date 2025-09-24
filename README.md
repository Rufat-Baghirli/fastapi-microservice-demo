# FastAPI Asynchronous Microservice

A comprehensive backend project built with FastAPI and Celery to demonstrate proficiency in building a scalable, microservices-based architecture. This repository serves as a portfolio piece showcasing an advanced understanding of modern backend technologies and CI/CD practices.

## Technologies Used

* **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python.
* **Celery**: An asynchronous task queue used for handling long-running background tasks.
* **RabbitMQ**: A robust message broker for communication between services.
* **Redis**: Used as both a Celery result backend and a high-performance cache.
* **PostgreSQL**: A powerful, open-source relational database.
* **Alembic**: A lightweight database migration tool for managing schema changes in PostgreSQL.
* **Docker & Docker Compose**: For containerization, ensuring a consistent development and production environment.
* **GitHub Actions**: For an automated Continuous Integration (CI) and Continuous Deployment (CD) pipeline.

## Architecture

This project adopts a microservices architecture to separate core functionalities.
* **Web Service**: A FastAPI application that handles API requests and dispatches asynchronous tasks to the message queue.
* **Worker Service**: A Celery worker that processes the tasks queued by the web service.
* **Message Broker**: RabbitMQ facilitates seamless, asynchronous communication between the web and worker services.

This design allows each service to be developed, scaled, and deployed independently, ensuring high performance and reliability.

## Getting Started

Follow these steps to get the project up and running on your local machine.

### Prerequisites

You need to have Docker and Docker Compose installed.

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/Rufat-Baghirli/fastapi-microservice-demo.git
    cd fastapi-microservice-demo
    ```

2.  Create your `.env.dev` file for local environment variables:
    (See `.env.dev.example` for a template)
    ```bash
    cp .env.dev.example .env.dev
    ```

3.  Build and run the containers using Docker Compose:
    ```bash
    docker-compose -f docker-compose.dev.yml up --build -d
    ```

### Accessing the Services

* **API**: The FastAPI application will be available at `http://localhost:8000`.
* **RabbitMQ Dashboard**: You can access the management dashboard at `http://localhost:15672` using the default `guest`/`guest` credentials.
* **PostgreSQL**: The database will be running on `localhost:5432`.

## CI/CD Workflow

This project is configured with a complete CI/CD pipeline using GitHub Actions.
* Pushes to any branch trigger a build and test process.
* Pushes to the `main` branch automatically trigger a deployment to the production server.

## License

This project is licensed under the MIT License.