from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid, os, subprocess
from app import database, models, crud, schemas
from sqlalchemy import func
from importlib import resources
import sys

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # endpoint/
APP_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../"))  # về tới thư mục app/
TTS_FOLDER = os.path.join(APP_DIR, "utils", "TTS")  # app/utils/TTS

PREFIX_PATH = os.path.join(TTS_FOLDER, "prefix", "prefix.mp3")
PREFIX_PATH_TAP = os.path.join(TTS_FOLDER, "prefix", "prefix_tap.mp3")
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

@router.post("/old", response_class=FileResponse)
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
    data: schemas.CounterUpsertRequestTTS,
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    # Lấy ID xã
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)

    if data.counter_id == 0:
        max_id = db.query(func.max(models.Counter.id))\
                   .filter(models.Counter.tenxa_id == tenxa_id)\
                   .scalar() or 0
        new_id = max_id + 1
        data.counter_id = new_id
    # Tìm quầy
    #counter = db.query(models.Counter).filter(
    #    models.Counter.id == data.counter_id,
    #    models.Counter.tenxa_id == tenxa_id
    #).first()
    #if not counter:
    #    raise HTTPException(status_code=404, detail="Không tìm thấy quầy")

    # Tạo nội dung
    text = f"Đến quầy số {data.counter_id}: {data.name}"
    tts = gTTS(text, lang='vi')

    # Lưu vào memory (BytesIO)
    mp3_io = BytesIO()
    tts.write_to_fp(mp3_io)
    mp3_io.seek(0)
    audio_bytes = mp3_io.read()

    # Xoá bản ghi cũ (nếu có)
    db.query(models.TTSAudio).filter(
        models.TTSAudio.tenxa_id == tenxa_id,
        models.TTSAudio.counter_id == data.counter_id
    ).delete(synchronize_session=False)

    # Ghi bản mới vào PostgreSQL
    new_audio = models.TTSAudio(
        tenxa_id=tenxa_id,
        counter_id=data.counter_id,
        audio_data=audio_bytes,
        created_at=datetime.utcnow()
    )
    db.add(new_audio)
    db.commit()

    return {
        "detail": "Tạo và lưu file thành công",
        #"counter_name": counter.name
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

import os
import sys
import uuid
import shutil
import tempfile
import subprocess
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app import crud, models, schemas

def get_base_dir() -> str:
    # Nếu chạy bằng pyz thì sys.argv[0] sẽ là file .pyz
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def safe_path(path: str) -> str:
    return os.path.abspath(path)


def run_ffmpeg(args: list, ffmpeg_path: str):
    """
    Wrapper chạy ffmpeg với path tuyệt đối, in stderr khi có lỗi.
    """
    cmd = [ffmpeg_path] + args
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"FFmpeg failed: {' '.join(cmd)}\n{result.stderr}"
        )
    return result


@router.post("/", response_class=FileResponse)
def generate_tts(
    request: TTSRequest,
    background_tasks: BackgroundTasks,
    tenxa: str = Query(...),
    db: Session = Depends(get_db)
):
    base_dir = get_base_dir()
    ffmpeg_path = os.path.join(base_dir, "ffmpeg.exe")
    tts_dir = os.path.join(base_dir, "TTS")

    if not os.path.exists(ffmpeg_path):
        raise HTTPException(status_code=500, detail=f"ffmpeg.exe not found at {ffmpeg_path}")

    # Lấy tenxa_id
    tenxa_id = crud.get_tenxa_id_from_slug(db, tenxa)

    # Lấy counter
    counter = db.query(models.Counter).filter(
        models.Counter.tenxa_id == tenxa_id,
        models.Counter.id == request.counter_id
    ).first()
    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")

    # Chọn file prefix
    if tenxa_id in (0,):
        prefix = os.path.join(tts_dir, "prefix", "prefix.mp3")
    else:
        prefix = os.path.join(tts_dir, "prefix", "prefix_tap.mp3")

    number = os.path.join(tts_dir, "numbers", f"{request.ticket_number}.mp3")

    # Lấy audio counter từ DB
    audio_record = db.query(models.TTSAudio).filter(
        models.TTSAudio.tenxa_id == tenxa_id,
        models.TTSAudio.counter_id == request.counter_id
    ).order_by(models.TTSAudio.created_at.desc()).first()

    if not audio_record:
        raise HTTPException(status_code=404, detail="Missing audio file in DB for counter")

    # Tạo file tạm counter
    counter_file_path = os.path.join(base_dir, f"counter_{uuid.uuid4().hex}.mp3")
    with open(counter_file_path, "wb") as f:
        f.write(audio_record.audio_data)

    # Kiểm tra tồn tại file local
    for path in [prefix, number]:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Missing audio file: {os.path.basename(path)}")

    # Chuẩn hóa tất cả file về wav mono 44100Hz
    temp_dir = tempfile.mkdtemp(prefix="tts_norm_")
    normalized_files = []
    try:
        for src in [prefix, number, counter_file_path]:
            norm_file = os.path.join(temp_dir, f"{uuid.uuid4().hex}.wav")
            run_ffmpeg(
                [
                    "-y",
                    "-i", safe_path(src),
                    "-ar", "44100", "-ac", "1",
                    norm_file
                ],
                ffmpeg_path
            )
            normalized_files.append(norm_file)

        # Tạo file list.txt
        list_file = os.path.join(temp_dir, "list.txt")
        with open(list_file, "w", encoding="utf-8") as f:
            for nf in normalized_files:
                # ffmpeg concat yêu cầu path forward slash
                f.write(f"file '{nf.replace(os.sep, '/')}'\n")

        # Xuất mp3 cuối
        output_file = os.path.join(base_dir, f"tts_{uuid.uuid4().hex}.mp3")
        run_ffmpeg(
            [
                "-y",
                "-f", "concat", "-safe", "0",
                "-i", list_file,
                "-c:a", "libmp3lame", "-q:a", "2",
                output_file
            ],
            ffmpeg_path
        )

    finally:
        # cleanup file counter tạm
        if os.path.exists(counter_file_path):
            background_tasks.add_task(lambda: os.remove(counter_file_path))
        # cleanup thư mục tạm
        if os.path.exists(temp_dir):
            background_tasks.add_task(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

    # cleanup file output sau khi gửi
    background_tasks.add_task(lambda: os.remove(output_file))

    return FileResponse(output_file, media_type="audio/mpeg", filename=os.path.basename(output_file))