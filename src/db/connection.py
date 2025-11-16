# src/db/connection.py
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def load_env():
    """
    프로젝트 루트에 있는 .env를 로드한다.
    (src/ 안에서 실행해도 잘 찾도록 상대 경로 처리)
    """
    # 현재 파일: .../src/db/connection.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]  # car-market-trend/
    env_path = project_root / ".env"

    if env_path.exists():
        load_dotenv(env_path)
    else:
        # .env가 없어도 그냥 진행은 하되, 나중에 에러가 나면 바로 확인 가능
        pass


def get_engine(echo: bool = False) -> Engine:
    """
    SQLAlchemy Engine 생성
    """
    load_env()

    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "car_trend")

    # mysql+pymysql URL 구성
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4"

    engine = create_engine(
        url,
        echo=echo,       # True로 두면 실행되는 SQL 출력
        future=True,     # SQLAlchemy 2.x 스타일
    )
    return engine