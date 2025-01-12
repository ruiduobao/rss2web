from sqlalchemy import create_engine, text
import time


def test_sqlalchemy():
    """使用 SQLAlchemy 测试连接"""
    try:
        print("\nTesting connection with SQLAlchemy...")
        engine = create_engine("postgresql://ruiduobao:ruiduobao@139.196.52.108:5432/postgres")
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT NOW()")).fetchone()
            print(f"Connection successful! Current time: {result[0]}")
    except Exception as e:
        print(f"SQLAlchemy connection error: {str(e)}")

if __name__ == "__main__":
    test_sqlalchemy() 