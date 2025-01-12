from db_models import Base
from sqlalchemy import create_engine

# 创建数据库连接
db_url = "你的数据库链接"
engine = create_engine(db_url)

# 删除所有表
Base.metadata.drop_all(engine)

# 重新创建所有表
Base.metadata.create_all(engine)

print("Database tables have been reset successfully!") 