from celery import Celery
import os

celery_app = Celery(
    "worker",
    broker=os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    include=['app.tasks.email']
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    imports=['app.tasks.email'],
)