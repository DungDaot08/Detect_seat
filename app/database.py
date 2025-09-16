from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:123@localhost/kiosk_db"
#SQLALCHEMY_DATABASE_URL = "postgresql://detect_seat_user:ixRpspwrkGkn4ylMjo222PIDFrVJghfD@dpg-d1r60amr433s739telgg-a/detect_seat"
#SQLALCHEMY_DATABASE_URL = "postgresql://detect_seat_user:ixRpspwrkGkn4ylMjo222PIDFrVJghfD@dpg-d1r60amr433s739telgg-a.oregon-postgres.render.com/detect_seat"
#SQLALCHEMY_DATABASE_URL = "postgresql://lstd:OPBoSaPESeIvrXWCiVCfxUb5TvyST0p8@dpg-d2ok600gjchc73erp7q0-a.oregon-postgres.render.com/lstd_zaup"
SQLALCHEMY_DATABASE_URL = "postgresql://lstd:DMYteWaJh8kAHhGXw6FAwp5lqnKSIs8A@dpg-d2ot633ipnbc73a7ivgg-a/lstd_dz27"
#SQLALCHEMY_DATABASE_URL = "postgresql://hcc_test_n4kv_user:yIzoeFfgAKJeCQoAtZbe5UXqIbSc1KAQ@dpg-d25cukadbo4c73bfspg0-a.oregon-postgres.render.com/hcc_test_n4kv"
#engine = create_engine(SQLALCHEMY_DATABASE_URL)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=40,        # giữ thường trực 20 connections
    max_overflow=40,     # có thể mở thêm tối đa 20 khi quá tải
    pool_timeout=30,     # chờ 30s nếu pool full
    pool_recycle=1800,   # reset sau 30 phút
    pool_pre_ping=True   # kiểm tra connection sống
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#SQLALCHEMY_STATS_URL = "postgresql://lstd:DMYteWaJh8kAHhGXw6FAwp5lqnKSIs8A@dpg-d2ot633ipnbc73a7ivgg-a.oregon-postgres.render.com/lstd_dz27"
#engine_stats = create_engine(SQLALCHEMY_STATS_URL)
#SessionStats = sessionmaker(autocommit=False, autoflush=False, bind=engine_stats)


Base = declarative_base()

