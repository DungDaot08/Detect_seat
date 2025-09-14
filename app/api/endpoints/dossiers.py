from fastapi import FastAPI, HTTPException
import requests
import os
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks

router = APIRouter()
# Config
TOKEN_URL = "https://ssodvc.tuyenquang.gov.vn/auth/realms/digo/protocol/openid-connect/token"
DOSSIER_URL = "https://apiigate.tuyenquang.gov.vn/pa/dossier/search"

# Tài khoản test (nếu cần bạn chuyển thành biến môi trường để bảo mật)
CLIENT_ID = "test-public"
USERNAME = "duytc.hgg"
PASSWORD = "Cntt@135"

@router.get("/dossiers")
def get_dossiers():
    # 1. Lấy access token
    token_payload = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "username": USERNAME,
        "password": PASSWORD
    }

    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = requests.post(TOKEN_URL, data=token_payload, headers=token_headers)

    if token_response.status_code != 200:
        raise HTTPException(status_code=token_response.status_code, detail="Không lấy được token")

    token = token_response.json().get("access_token")
    if not token:
        raise HTTPException(status_code=500, detail="Token rỗng")

    # 2. Gọi API danh sách hồ sơ
    dossier_params = {
        "page": 0,
        "size": 50,
        "spec": "page",
        "ancestor-agency-id": "6853b890edeb9d6b96aac021",
        "sort": "updatedDate,desc",
        "remove-status": 18,
        "isAgencySearch": "true",
        "task-status-id": "642cee9d3181093fe0519363"
    }
    dossier_headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    dossier_response = requests.get(DOSSIER_URL, params=dossier_params, headers=dossier_headers)
    if dossier_response.status_code != 200:
        raise HTTPException(status_code=dossier_response.status_code, detail="Không lấy được danh sách hồ sơ")

    dossiers = dossier_response.json().get("content", [])

    # 3. Lọc các trường cần thiết
    results = []
    for d in dossiers:
        code = d.get("code")
        fullname = d.get("applicant", {}).get("data", {}).get("fullname")
        applied_date = d.get("appliedDate")
        completed_date = d.get("completedDate")
        results.append({
            "code": code,
            "ho_ten": fullname,
            "ngay_nop": applied_date,
            "ngay_co_ket_qua": completed_date
        })

    return {"total": len(results), "dossiers": results}

import requests, time, os

# Cache token
_token_cache = {
    "access_token": None,
    "expires_at": 0
}

def get_access_token():
    now = int(time.time())
    # Nếu token còn hạn thì trả về luôn
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    # Nếu hết hạn thì xin token mới
    payload = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "username": USERNAME,
        "password": PASSWORD
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(TOKEN_URL, data=payload, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Không lấy được token")

    data = resp.json()
    access_token = data.get("access_token")
    expires_in = data.get("expires_in", 300)  # thường 300s = 5 phút

    if not access_token:
        raise HTTPException(status_code=500, detail="Token rỗng")

    # Lưu token + thời gian hết hạn (trừ đi 30s để an toàn)
    _token_cache["access_token"] = access_token
    _token_cache["expires_at"] = now + expires_in - 30

    return access_token

@router.get("/dossiers1")
def get_dossiers1():
    token = get_access_token()

    params = {
        "page": 0,
        "size": 50,
        "spec": "page",
        "ancestor-agency-id": "6853b890edeb9d6b96aac021",
        "sort": "updatedDate,desc",
        "remove-status": 18,
        "isAgencySearch": "true",
        "task-status-id": "642cee9d3181093fe0519363"
    }
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}

    resp = requests.get(DOSSIER_URL, params=params, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Không lấy được danh sách hồ sơ")

    dossiers = resp.json().get("content", [])
    results = [
        {
            "code": d.get("code"),
            "ho_ten": d.get("applicant", {}).get("data", {}).get("fullname"),
            "ngay_nop": d.get("appliedDate"),
            "ngay_co_ket_qua": d.get("completedDate")
        }
        for d in dossiers
    ]

    return {"total": len(results), "dossiers": results}
