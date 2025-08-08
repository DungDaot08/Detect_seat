from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:123@localhost/kiosk_db"
SQLALCHEMY_DATABASE_URL = "postgresql://detect_seat_user:ixRpspwrkGkn4ylMjo222PIDFrVJghfD@dpg-d1r60amr433s739telgg-a/detect_seat"
#SQLALCHEMY_DATABASE_URL = "postgresql://detect_seat_user:ixRpspwrkGkn4ylMjo222PIDFrVJghfD@dpg-d1r60amr433s739telgg-a.oregon-postgres.render.com/detect_seat"
#SQLALCHEMY_DATABASE_URL = "postgresql://hcc_test_n4kv_user:yIzoeFfgAKJeCQoAtZbe5UXqIbSc1KAQ@dpg-d25cukadbo4c73bfspg0-a/hcc_test_n4kv"
#SQLALCHEMY_DATABASE_URL = "postgresql://hcc_test_n4kv_user:yIzoeFfgAKJeCQoAtZbe5UXqIbSc1KAQ@dpg-d25cukadbo4c73bfspg0-a.oregon-postgres.render.com/hcc_test_n4kv"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
