from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid, os, subprocess

from app import database, models, crud

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # endpoint/
APP_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../"))  # về tới thư mục app/
TTS_FOLDER = os.path.join(APP_DIR, "utils", "TTS")  # app/utils/TTS

PREFIX_PATH = os.path.join(TTS_FOLDER, "prefix", "prefix.mp3")
NUMBERS_PATH = os.path.join(TTS_FOLDER, "numbers")
COUNTER_PATH = os.path.join(TTS_FOLDER, "counter_audio")

#print("PREFIX_PATH:", PREFIX_PATH)
#print("NUMBERS_PATH:", NUMBERS_PATH)
#print("COUNTER_PATH:", COUNTER_PATH)

class TTSRequest(BaseModel):
    counter_id: int
    ticket_number: int

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_class=FileResponse)
def generate_tts(
    request: TTSRequest,
    background_tasks: BackgroundTasks,
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)

    # Lấy thông tin quầy
    counter = db.query(models.Counter).filter(
        models.Counter.tenxa_id == tenxa_id,
        models.Counter.id == request.counter_id
    ).first()

    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")


    # Đường dẫn 3 file cần ghép
    prefix = PREFIX_PATH
    number = os.path.join(NUMBERS_PATH, f"{request.ticket_number}.mp3")
    print("Number file:", number)
    print("Exists:", os.path.exists(number))
    counter_file = os.path.join(COUNTER_PATH, f"Quay{request.counter_id}_xa{tenxa_id}.mp3")
    print("Number file:", counter_file)
    print("Exists:", os.path.exists(counter_file))

    # Kiểm tra tồn tại
    for path in [prefix, number, counter_file]:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Missing audio file: {os.path.basename(path)}")

    # Tạo file tạm
    filename = f"tts_{uuid.uuid4().hex}.mp3"

    # Ghép file bằng ffmpeg
    list_path = f"temp_{uuid.uuid4().hex}.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        f.write(f"file '{prefix}'\n")
        f.write(f"file '{number}'\n")
        f.write(f"file '{counter_file}'\n")

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", filename],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Failed to generate audio")

    # Dọn rác
    background_tasks.add_task(lambda: os.remove(filename))
    background_tasks.add_task(lambda: os.remove(list_path))

    return FileResponse(filename, media_type="audio/mpeg", filename=filename)

from fastapi import UploadFile
from gtts import gTTS
from sqlalchemy import insert
from datetime import datetime
from app import models
from io import BytesIO
from fastapi.responses import StreamingResponse

@router.post("/generate_counter_audio")
def generate_counter_audio(
    counter_id: int,
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    # Lấy ID xã
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)

    # Tìm quầy
    counter = db.query(models.Counter).filter(
        models.Counter.id == counter_id,
        models.Counter.tenxa_id == tenxa_id
    ).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Không tìm thấy quầy")

    # Tạo nội dung
    text = f"Đến quầy số {counter_id}: {counter.name}"
    tts = gTTS(text, lang='vi')

    # Lưu vào memory (BytesIO)
    mp3_io = BytesIO()
    tts.write_to_fp(mp3_io)
    mp3_io.seek(0)
    audio_bytes = mp3_io.read()

    # Xoá bản ghi cũ (nếu có)
    db.query(models.TTSAudio).filter(
        models.TTSAudio.tenxa_id == tenxa_id,
        models.TTSAudio.counter_id == counter_id
    ).delete(synchronize_session=False)

    # Ghi bản mới vào PostgreSQL
    new_audio = models.TTSAudio(
        tenxa_id=tenxa_id,
        counter_id=counter_id,
        audio_data=audio_bytes,
        created_at=datetime.utcnow()
    )
    db.add(new_audio)
    db.commit()

    return {
        "detail": "Tạo và lưu file thành công",
        "counter_name": counter.name
    }


@router.get("/export_counter_audio", response_class=StreamingResponse)
def export_counter_audio(
    tenxa: str = Query(...),
    counter_id: int = Query(...),
    db: Session = Depends(get_db)
):
    # Lấy ID xã từ slug
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)

    # Tìm file audio mới nhất cho quầy này
    audio_record = db.query(models.TTSAudio).filter(
        models.TTSAudio.tenxa_id == tenxa_id,
        models.TTSAudio.counter_id == counter_id
    ).order_by(models.TTSAudio.created_at.desc()).first()

    if not audio_record:
        raise HTTPException(status_code=404, detail="Không tìm thấy file ghi âm")

    # Trả về file dưới dạng streaming .mp3
    audio_stream = BytesIO(audio_record.audio_data)
    return StreamingResponse(
        audio_stream,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"attachment; filename=quay_{counter_id}_xa_{tenxa}.mp3"
        }
    )

@router.post("/new", response_class=FileResponse)
def generate_tts(
    request: TTSRequest,
    background_tasks: BackgroundTasks,
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)

    # Lấy thông tin quầy
    counter = db.query(models.Counter).filter(
        models.Counter.tenxa_id == tenxa_id,
        models.Counter.id == request.counter_id
    ).first()

    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")

    # Đường dẫn 2 file local
    prefix = PREFIX_PATH
    number = os.path.join(NUMBERS_PATH, f"{request.ticket_number}.mp3")

    # Lấy audio từ DB
    audio_record = db.query(models.TTSAudio).filter(
        models.TTSAudio.tenxa_id == tenxa_id,
        models.TTSAudio.counter_id == request.counter_id
    ).order_by(models.TTSAudio.created_at.desc()).first()

    if not audio_record:
        raise HTTPException(status_code=404, detail="Missing audio file in DB for counter")

    # Ghi file counter ra đĩa tạm
    counter_file_path = f"counter_{uuid.uuid4().hex}.mp3"
    with open(counter_file_path, "wb") as f:
        f.write(audio_record.audio_data)

    # Kiểm tra tồn tại 2 file local
    for path in [prefix, number]:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Missing audio file: {os.path.basename(path)}")

    # Tạo danh sách file ghép
    output_file = f"tts_{uuid.uuid4().hex}.mp3"
    list_path = f"temp_{uuid.uuid4().hex}.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        f.write(f"file '{prefix}'\n")
        f.write(f"file '{number}'\n")
        f.write(f"file '{counter_file_path}'\n")

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", output_file],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Failed to generate audio")

    # Dọn rác
    background_tasks.add_task(lambda: os.remove(output_file))
    background_tasks.add_task(lambda: os.remove(list_path))
    background_tasks.add_task(lambda: os.remove(counter_file_path))

    return FileResponse(output_file, media_type="audio/mpeg", filename=output_file)
