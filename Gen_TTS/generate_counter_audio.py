import csv
import os
from gtts import gTTS

# Đường dẫn file CSV
CSV_FILE = "config_quay.csv"  # Đặt đúng tên file CSV của bạn

# Thư mục lưu file mp3
OUTPUT_DIR = "counter_audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Đọc và xử lý file CSV
with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        so_quay = row['Quầy số'].strip()
        ten_quay = row['Tên quầy'].strip()
        xa = row['Xã'].strip()

        # Câu thoại cần đọc
        text = f"Đến quầy số {so_quay} {ten_quay}"

        # Tạo file âm thanh
        filename = f"Quay{so_quay}_xa{xa}.mp3"
        filepath = os.path.join(OUTPUT_DIR, filename)

        tts = gTTS(text=text, lang='vi')
        tts.save(filepath)

        print(f"✅ Đã tạo: {filepath}")
