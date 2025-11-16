# src/db/test_connection.py
from sqlalchemy import text

from .connection import get_engine


def main():
    engine = get_engine(echo=False)

    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = result.fetchall()

    print("=== Tables in DB ===")
    for row in tables:
        # MySQL SHOW TABLES 결과는 ('table_name',) 이런 튜플
        print(row[0])


if __name__ == "__main__":
    main()
