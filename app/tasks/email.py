from app.tasks.worker import celery_app
import time

@celery_app.task(name="app.tasks.email.send_email")
def send_email(to: str, subject: str, body: str):
    time.sleep(2)
    print(f"[worker] Sent email to {to} subject={subject}")
    return {"to": to, "subject": subject, "status": "sent"}
