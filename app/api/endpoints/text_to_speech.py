from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from gtts import gTTS
from sqlalchemy.orm import Session
import uuid, os
from app import database, models

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TTSRequest(BaseModel):
    counter_id: int
    ticket_number: int

@router.post("/", response_class=FileResponse)
def generate_tts(request: TTSRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    counter = db.query(models.Counter).filter(models.Counter.id == request.counter_id).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    
    # Tạo nội dung lời thoại
    text = f"Xin mời khách hàng số {request.ticket_number} đến quầy số {request.counter_id} - {counter.name}"

    # Tạo file mp3
    filename = f"voice_{uuid.uuid4().hex}.mp3"
    tts = gTTS(text=text, lang='vi')
    tts.save(filename)

    # Xoá file sau khi gửi
    background_tasks.add_task(lambda: os.remove(filename))

    return FileResponse(filename, media_type="audio/mpeg", filename=filename)
