import json
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_models import Base, Journal, Article, Tag, Comment, User
from datetime import datetime
import openai
from typing import Tuple, Optional
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select

class DatabaseManager:
    def __init__(self):
        # 数据库连接URL
        self.db_url = "你的数据库链接"
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # 配置 OpenAI
        openai.api_key = "sk-LsJwuRBc4eikc3Ir002fD6B9F89349E3A65258650a88F3F6"
        openai.base_url = "https://api.gpt.ge/v1/"

    def init_db(self):
        """初始化数据库表"""
        Base.metadata.create_all(self.engine)
        
    def add_journal(self, name, rss_url, description=""):
        """添加期刊"""
        session = self.Session()
        journal = Journal(name=name, rss_url=rss_url, description=description)
        session.add(journal)
        session.commit()
        journal_id = journal.id
        session.close()
        return journal_id
    def get_or_create_journal(self, name, rss_url, description=""):
        """获取现有期刊或创建新期刊"""
        session = self.Session()
        
        # 查找现有期刊
        journal = session.query(Journal).filter_by(rss_url=rss_url).first()
        
        if journal:
            journal_id = journal.id
            session.close()
            return journal_id
            
        # 创建新期刊
        journal = Journal(
            name=name,
            rss_url=rss_url,
            description=description
        )
        session.add(journal)
        session.commit()
        journal_id = journal.id
        session.close()
        return journal_id
    
    def translate_and_save_article(self, title: str, summary: str, max_retries: int = 6):
        """翻译单个文章并返回结果"""
        for attempt in range(max_retries):
            try:
                prompt = f"""请将以下英文标题和摘要翻译成中文：
                
                标题：{title}
                摘要：{summary}
                
                请按以下格式返回JSON：
                {{
                    "title": "中文标题",
                    "abstract": "中文摘要"
                }}"""
                
                completion = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=2000
                )
                
                response = completion.choices[0].message.content
                translation = json.loads(response)
                
                # 验证翻译结果不为空
                if translation['title'].strip() and translation['abstract'].strip():
                    print(f"文章翻译成功 (尝试 {attempt + 1}/{max_retries})")
                    return translation['title'], translation['abstract']
                else:
                    raise ValueError("翻译结果为空")
                    
            except Exception as e:
                print(f"翻译失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 失败后等待2秒再重试
                    continue
                    
        print(f"所有翻译尝试都失败了，使用原文")
        return None, None

    def add_article(self, journal_id, article_data):
        """添加文章（立即翻译和保存）"""
        session = self.Session()
        
        try:
            # 检查文章是否已存在
            existing_article = session.query(Article).filter_by(doi=article_data['doi']).first()
            if existing_article:
                print(f"文章已存在: {article_data['title'][:50]}...")
                session.close()
                return None
            
            # 立即翻译当前文章
            print(f"开始翻译文章: {article_data['title'][:50]}...")
            title_zh, summary_zh = self.translate_and_save_article(
                article_data['title'],
                article_data['summary']
            )
            
            # 转换发布日期字符串为datetime对象
            published_date = datetime.strptime(article_data['published'], '%Y-%m-%d')
            
            # 创建并立即保存文章
            article = Article(
                title=article_data['title'],
                title_zh=title_zh,  # 如果翻译失败，这里会是 None
                volume=article_data.get('volume', ''),
                pages=article_data.get('pages', ''),
                authors=json.dumps(article_data['authors']),
                published_date=published_date,
                doi=article_data['doi'],
                link=article_data['link'],
                summary=article_data['summary'],
                summary_zh=summary_zh,  # 如果翻译失败，这里会是 None
                journal_id=journal_id
            )
            
            session.add(article)
            session.commit()
            article_id = article.id
            
            print(f"文章保存成功 (ID: {article_id})")
            if title_zh and summary_zh:
                print(f"中文标题: {title_zh[:50]}...")
            else:
                print("使用原文（翻译失败）")
                
            session.close()
            return article_id
            
        except Exception as e:
            session.rollback()
            print(f"添加文章错误：{str(e)}")
            session.close()
            return None

    def article_exists(self, doi):
        """检查文章是否已存在"""
        session = self.Session()
        try:
            exists = session.query(Article).filter_by(doi=doi).first() is not None
            return exists
        finally:
            session.close()

    async def add_article_async(self, journal_id, article_data):
        """异步添加文章"""
        # 创建新的会话
        session = self.Session()
        
        try:
            # 翻译标题和摘要
            title_zh, summary_zh = await self.translate_article_async(
                article_data['title'],
                article_data['summary']
            )
            
            # 转换发布日期
            published_date = datetime.strptime(article_data['published'], '%Y-%m-%d')
            
            # 创建文章对象
            article = Article(
                title=article_data['title'],
                title_zh=title_zh,
                volume=article_data.get('volume', ''),
                pages=article_data.get('pages', ''),
                authors=json.dumps(article_data['authors']),
                published_date=published_date,
                doi=article_data['doi'],
                link=article_data['link'],
                summary=article_data['summary'],
                summary_zh=summary_zh,
                journal_id=journal_id
            )
            
            session.add(article)
            await session.commit()
            article_id = article.id
            return article_id
            
        except Exception as e:
            await session.rollback()
            print(f"添加文章错误：{str(e)}")
            return None
            
        finally:
            await session.close()

    async def translate_article_async(self, title: str, summary: str, max_retries: int = 3):
        """异步翻译文章"""
        for attempt in range(max_retries):
            try:
                prompt = f"""请将以下英文标题和摘要翻译成中文：
                
                标题：{title}
                摘要：{summary}
                
                请按以下格式返回JSON：
                {{
                    "title": "中文标题",
                    "abstract": "中文摘要"
                }}"""
                
                completion = await openai.chat.completions.acreate(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=2000
                )
                
                response = completion.choices[0].message.content
                translation = json.loads(response)
                
                if translation['title'].strip() and translation['abstract'].strip():
                    print(f"翻译成功 (尝试 {attempt + 1}/{max_retries})")
                    return translation['title'], translation['abstract']
                    
            except Exception as e:
                print(f"翻译失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
        
        return None, None

    def add_article_without_translation(self, article_data):
        """添加文章（不包含翻译）"""
        session = self.Session()
        
        try:
            # 检查文章是否已存在
            existing_article = session.query(Article).filter_by(doi=article_data['doi']).first()
            if existing_article:
                session.close()
                return None
            
            # 转换发布日期字符串为datetime对象
            published_date = datetime.strptime(article_data['published'], '%Y-%m-%d')
            
            # 创建新文章
            article = Article(
                title=article_data['title'],
                title_zh=None,  # 初始为空
                volume=article_data.get('volume', ''),
                pages=article_data.get('pages', ''),
                authors=json.dumps(article_data.get('authors', [])),
                published_date=published_date,
                doi=article_data['doi'],
                link=article_data['link'],
                summary=article_data['summary'],
                summary_zh=None,  # 初始为空
                journal_id=article_data['journal_id']
            )
            
            session.add(article)
            session.commit()
            article_id = article.id
            session.close()
            return article_id
            
        except Exception as e:
            session.rollback()
            print(f"添加文章错误：{str(e)}")
            session.close()
            return None

    def get_untranslated_articles(self, limit=10):
        """获取未翻译的文章"""
        session = self.Session()
        try:
            articles = session.query(Article)\
                .filter(Article.title_zh.is_(None))\
                .limit(limit)\
                .all()
            return articles
        finally:
            session.close()

    def translate_article(self, title: str, summary: str, max_retries: int = 3):
        """翻译文章内容"""
        for attempt in range(max_retries):
            try:
                prompt = f"""请将以下英文标题和摘要翻译成中文：
                
                标题：{title}
                摘要：{summary}
                
                请按以下格式返回JSON：
                {{
                    "title": "中文标题",
                    "abstract": "中文摘要"
                }}"""
                
                completion = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=2000
                )
                
                response = completion.choices[0].message.content
                translation = json.loads(response)
                
                if translation['title'].strip() and translation['abstract'].strip():
                    return translation['title'], translation['abstract']
                    
            except Exception as e:
                print(f"翻译失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                    
        return None, None

    def update_article_translation(self, article_id: int, title_zh: str, summary_zh: str):
        """更新文章的翻译"""
        session = self.Session()
        try:
            article = session.query(Article).filter_by(id=article_id).first()
            if article:
                article.title_zh = title_zh
                article.summary_zh = summary_zh
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"更新翻译错误：{str(e)}")
            return False
        finally:
            session.close()

    def get_or_create_journal(self, name, rss_url):
        """获取或创建期刊"""
        session = self.Session()
        try:
            journal = session.query(Journal).filter_by(name=name).first()
            if not journal:
                journal = Journal(name=name, rss_url=rss_url)
                session.add(journal)
                session.commit()
            return journal.id
        finally:
            session.close()
