from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ProcedureBase(BaseModel):
    name: str
    field_id: int

class Procedure(ProcedureBase):
    id: int
    class Config:
        orm_mode = True

class Counter(BaseModel):
    id: int
    name: str
    status: Optional[str] = "active" 

    class Config:
        orm_mode = True

class ProcedureSearchResponse(BaseModel):
    id: int
    name: str
    field_id: int
    counters: List[Counter]

class TicketCreate(BaseModel):
    counter_id: int

class Ticket(BaseModel):
    id: int
    number: int
    counter_id: int
    created_at: datetime
    status: str
    called_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        orm_mode = True
class TicketUpdateStatus(BaseModel):
    status: str
class SeatType(str, Enum):
    officer = "officer"
    client = "client"
    
class SeatBase(BaseModel):
    name: str
    type: SeatType
    counter_id: int
    status: Optional[bool] = False

class SeatCreate(SeatBase):
    pass

class SeatUpdate(BaseModel):
    status: bool

class Seat(SeatBase):
    id: int
    last_empty_time: Optional[datetime]

    class Config:
        orm_mode = True

class SeatPublic(BaseModel):
    id: int
    status: bool
    type: str
    counter_id: int

    class Config:
        orm_mode = True
class CalledTicket(BaseModel):
    number: int
    counter_name: str
    tenxa: str
    class Config:
        orm_mode = True

class CounterPauseCreate(BaseModel):
    reason: str

class CounterPauseLog(BaseModel):
    id: int
    counter_id: int
    reason: str
    created_at: datetime
    start_time: datetime  # 🆕
    end_time: Optional[datetime] = None
    class Config:
        orm_mode = True
        
class Role(str, Enum):
    admin = "admin"
    leader = "leader"
    officer = "officer"

class UserBase(BaseModel):
    username: str
    full_name: Optional[str]
    role: Role
    counter_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    
class FooterBase(BaseModel):
    work_time: str
    hotline: str

class FooterCreate(FooterBase):
    pass

class FooterResponse(FooterBase):
    tenxa: str