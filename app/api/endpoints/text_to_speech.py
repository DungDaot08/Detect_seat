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

print("PREFIX_PATH:", PREFIX_PATH)
print("NUMBERS_PATH:", NUMBERS_PATH)
print("COUNTER_PATH:", COUNTER_PATH)

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
