from fastapi import APIRouter
from pydantic import BaseModel
from app.tasks.email import send_email

router = APIRouter(tags=["tasks"])

class EmailPayload(BaseModel):
    to: str
    subject: str
    body: str

@router.post("/send-email")
async def trigger_send_email(payload: EmailPayload):
    # .delay() sends task to the broker (non-blocking)
    task = send_email.delay(payload.to, payload.subject, payload.body)
    return {"task_id": task.id}

