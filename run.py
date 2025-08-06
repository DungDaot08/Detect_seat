import sys
import os

# Thêm thư mục gốc vào sys.path để Python có thể import "app"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        log_config=None, 
        use_colors=False
    )

