from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from gtts import gTTS
from sqlalchemy.orm import Session
import uuid, os
from app import database, models, crud

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

#@router.post("/", response_class=FileResponse)
#def generate_tts(request: TTSRequest, background_tasks: BackgroundTasks, tenxa: str = Query(...), db: Session = Depends(get_db)):
#    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
#    counter = db.query(models.Counter).filter(models.Counter.tenxa_id == tenxa_id).filter(models.Counter.id == request.counter_id).first()
#    if not counter:
#        raise HTTPException(status_code=404, detail="Counter not found")
    
    # Tạo nội dung lời thoại
#    text = f"Xin mời khách hàng số {request.ticket_number} đến quầy số {request.counter_id}: {counter.name}"

    # Tạo file mp3
#    filename = f"voice_{uuid.uuid4().hex}.mp3"
#    tts = gTTS(text=text, lang='vi')
#    tts.save(filename)

    # Xoá file sau khi gửi
#    background_tasks.add_task(lambda: os.remove(filename))

#    return FileResponse(filename, media_type="audio/mpeg", filename=filename)

import uuid
import os
import asyncio
import edge_tts
from fastapi import APIRouter, BackgroundTasks, Query, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app import crud, models
#from app.schemas import TTSRequest
#from app.database import get_db

router = APIRouter()

async def synthesize_edge_tts(text: str, filename: str):
    communicate = edge_tts.Communicate(text=text, voice="vi-VN-HoaiMyNeural")
    await communicate.save(filename)

@router.post("/", response_class=FileResponse)
def generate_tts(
    request: TTSRequest,
    background_tasks: BackgroundTasks,
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)
    counter = db.query(models.Counter).filter(
        models.Counter.tenxa_id == tenxa_id,
        models.Counter.id == request.counter_id
    ).first()

    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")

    # Nội dung thoại
    text = f"Xin mời khách hàng số {request.ticket_number} đến quầy số {request.counter_id}: {counter.name}"

    # Tên file mp3
    filename = f"voice_{uuid.uuid4().hex}.mp3"

    # Gọi edge-tts (bắt buộc chạy async)
    asyncio.run(synthesize_edge_tts(text, filename))

    # Xoá file sau khi gửi
    background_tasks.add_task(lambda: os.remove(filename))

    return FileResponse(filename, media_type="audio/mpeg", filename=filename)
