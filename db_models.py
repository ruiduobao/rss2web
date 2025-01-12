from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# 文章-标签关联表
article_tags = Table(
    'article_tags',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Journal(Base):
    __tablename__ = 'journals'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    rss_url = Column(String(500), nullable=False)
    description = Column(Text)
    articles = relationship("Article", back_populates="journal")

class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    title_zh = Column(String(500))  # 中文标题
    volume = Column(String(200))    # 增加长度
    pages = Column(String(200))     # 增加长度
    authors = Column(Text)
    published_date = Column(DateTime)
    doi = Column(String(100))
    link = Column(String(500))
    summary = Column(Text)
    summary_zh = Column(Text)
    journal_id = Column(Integer, ForeignKey('journals.id'))
    image_url = Column(String(500))
    
    journal = relationship("Journal", back_populates="articles")
    tags = relationship("Tag", secondary=article_tags)
    comments = relationship("Comment", back_populates="article")

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    article = relationship("Article", back_populates="comments")
    user = relationship("User")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(200))