from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime, func, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy import Enum as PgEnum
import enum

class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    procedures = relationship("Procedure", back_populates="field")
    counter_fields = relationship("CounterField", back_populates="field")  # Sửa lại cho khớp
    
class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    field_id = Column(Integer, ForeignKey("fields.id"))  # ✅ cần dòng này

    field = relationship("Field", back_populates="procedures")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, nullable=False)
    counter_id = Column(Integer, ForeignKey("counters.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    status = Column(String(20), default="waiting")

    counter = relationship("Counter", back_populates="tickets")
    
class Counter(Base):
    __tablename__ = "counters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    timeout_seconds = Column(Integer, default=60)
    status = Column(String(20), nullable=False, default="active")

    counter_fields = relationship("CounterField", back_populates="counter")
    seats = relationship("Seat", back_populates="counter", cascade="all, delete")
    tickets = relationship("Ticket", back_populates="counter", cascade="all, delete")
    users = relationship("User", back_populates="counter")

class CounterField(Base):
    __tablename__ = "counter_field"

    id = Column(Integer, primary_key=True, index=True)
    counter_id = Column(Integer, ForeignKey("counters.id"))
    field_id = Column(Integer, ForeignKey("fields.id"))

    __table_args__ = (UniqueConstraint('counter_id', 'field_id', name='uix_counter_field'),)

    counter = relationship("Counter", back_populates="counter_fields")
    field = relationship("Field", back_populates="counter_fields") 

class SeatType(str, enum.Enum):
    officer = "officer"
    client = "client"
    
class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    counter_id = Column(Integer, ForeignKey("counters.id"), nullable=False)
    type = Column(PgEnum(SeatType), nullable=False, default="client")
    status = Column(Boolean, default=False)  # True = Có người, False = Trống
    last_empty_time = Column(DateTime, nullable=True)

    counter = relationship("Counter", back_populates="seats")

class CounterPauseLog(Base):
    __tablename__ = "counter_pause_logs"

    id = Column(Integer, primary_key=True, index=True)
    counter_id = Column(Integer, ForeignKey("counters.id"), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    counter = relationship("Counter", backref="pause_logs")
    
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

    counter = relationship("Counter", back_populates="users")