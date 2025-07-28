from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:123@localhost/kiosk_db"
#SQLALCHEMY_DATABASE_URL = "postgresql://detect_seat_user:ixRpspwrkGkn4ylMjo222PIDFrVJghfD@dpg-d1r60amr433s739telgg-a/detect_seat"
SQLALCHEMY_DATABASE_URL = "postgresql://detect_seat_user:ixRpspwrkGkn4ylMjo222PIDFrVJghfD@dpg-d1r60amr433s739telgg-a.oregon-postgres.render.com/detect_seat"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
