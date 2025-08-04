from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime, func, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy import Enum as PgEnum
import enum

class Field(Base):
    __tablename__ = "fields"

    code = Column(Integer, primary_key=True, index=True)
    id = Column(Integer)
    name = Column(String, nullable=False)
    tenxa_id = Column(Integer, ForeignKey("tenxa.id"), nullable=False)

    procedures = relationship("Procedure", back_populates="field")
    counter_fields = relationship("CounterField", back_populates="field")  # Sửa lại cho khớp
    tenxa = relationship("Tenxa")
    
class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    field_id = Column(Integer, ForeignKey("fields.id"))  # ✅ cần dòng này
    tenxa_id = Column(Integer, ForeignKey("tenxa.id"), nullable=False)

    field = relationship("Field", back_populates="procedures")
    tenxa = relationship("Tenxa")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, nullable=False)
    counter_id = Column(Integer, ForeignKey("counters.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    status = Column(String(20), default="waiting")
    called_at = Column(DateTime, nullable=True, default=None)
    finished_at = Column(DateTime, nullable=True, default=None)
    tenxa_id = Column(Integer, ForeignKey("tenxa.id"), nullable=False)

    counter = relationship("Counter", back_populates="tickets")
    tenxa = relationship("Tenxa")
class Counter(Base):
    __tablename__ = "counters"

    code = Column(Integer, primary_key=True, index=True)
    id = Column(Integer)
    name = Column(String, nullable=False)
    timeout_seconds = Column(Integer, default=60)
    status = Column(String(20), nullable=False, default="active")
    tenxa_id = Column(Integer, ForeignKey("tenxa.id"), nullable=False)

    counter_fields = relationship("CounterField", back_populates="counter")
    seats = relationship("Seat", back_populates="counter", cascade="all, delete")
    tickets = relationship("Ticket", back_populates="counter", cascade="all, delete")
    users = relationship("User", back_populates="counter")
    tenxa = relationship("Tenxa")

class CounterField(Base):
    __tablename__ = "counter_field"

    id = Column(Integer, primary_key=True, index=True)
    counter_id = Column(Integer, ForeignKey("counters.id"))
    field_id = Column(Integer, ForeignKey("fields.id"))
    tenxa_id = Column(Integer, ForeignKey("tenxa.id"), nullable=False)

    __table_args__ = (UniqueConstraint('counter_id', 'field_id', name='uix_counter_field'),)

    counter = relationship("Counter", back_populates="counter_fields")
    field = relationship("Field", back_populates="counter_fields")
    tenxa = relationship("Tenxa") 

class SeatType(str, enum.Enum):
    officer = "officer"
    client = "client"

class SeatLog(Base):
    __tablename__ = "seat_logs"

    id = Column(Integer, primary_key=True, index=True)
    seat_id = Column(Integer, ForeignKey("seats.id"))
    old_status = Column(Boolean)
    new_status = Column(Boolean)
    timestamp = Column(DateTime, default=func.now())
    tenxa_id = Column(Integer, ForeignKey("tenxa.id"), nullable=False)

    seat = relationship("Seat", back_populates="logs")
    tenxa = relationship("Tenxa")
class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    counter_id = Column(Integer, ForeignKey("counters.id"), nullable=False)
    type = Column(PgEnum(SeatType), nullable=False, default="client")
    status = Column(Boolean, default=False)  # True = Có người, False = Trống
    last_empty_time = Column(DateTime, nullable=True)
    tenxa_id = Column(Integer, ForeignKey("tenxa.id"), nullable=False)

    counter = relationship("Counter", back_populates="seats")
    logs = relationship("SeatLog", back_populates="seat")
    tenxa = relationship("Tenxa")

class CounterPauseLog(Base):
    __tablename__ = "counter_pause_logs"

    id = Column(Integer, primary_key=True, index=True)
    counter_id = Column(Integer, ForeignKey("counters.id"), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    start_time = Column(DateTime, nullable=True, default=func.now())  # 🆕 thời gian bắt đầu pause
    end_time = Column(DateTime, nullable=True)
    tenxa_id = Column(Integer, ForeignKey("tenxa.id"), nullable=False)   

    counter = relationship("Counter", backref="pause_logs")
    tenxa = relationship("Tenxa")
    
class Role(str, enum.Enum):
    admin = "admin"
    leader = "leader"
    officer = "officer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String(100))
    role = Column(Enum(Role), nullable=False)
    is_active = Column(Boolean, default=True)
    counter_id = Column(Integer, ForeignKey("counters.id"), nullable=True)
    tenxa_id = Column(Integer, ForeignKey("tenxa.id"), nullable=False)

    counter = relationship("Counter", back_populates="users")
    tenxa = relationship("Tenxa")
    
class Tenxa(Base):
    __tablename__ = "tenxa"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    auto_call = Column(Boolean, default=False)
    
from sqlalchemy import Column, Integer, LargeBinary, DateTime
from sqlalchemy.sql import func
from app.database import Base

class TTSAudio(Base):
    __tablename__ = "tts_audio"

    id = Column(Integer, primary_key=True, index=True)
    tenxa_id = Column(Integer, nullable=False)
    counter_id = Column(Integer, nullable=False)
    audio_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class Footer(Base):
    __tablename__ = "footers"

    id = Column(Integer, primary_key=True, index=True)
    tenxa_id = Column(Integer, ForeignKey("tenxa.id"), unique=True, nullable=False)
    work_time = Column(String, nullable=True)
    hotline = Column(String, nullable=True)

    tenxa = relationship("Tenxa")  # nếu bạn có bảng `tenxa`
