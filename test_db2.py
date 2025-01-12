from sqlalchemy import create_engine, text
import time


def test_sqlalchemy():
    """使用 SQLAlchemy 测试本地 PostgreSQL 连接"""
    try:
        print("\nTesting connection with SQLAlchemy...")
        # 修改连接字符串为本地数据库
        engine = create_engine("你的数据库链接")
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT NOW()")).fetchone()
            print(f"Connection successful! Current time: {result[0]}")
    except Exception as e:
        print(f"SQLAlchemy connection error: {str(e)}")

if __name__ == "__main__":
    test_sqlalchemy() 