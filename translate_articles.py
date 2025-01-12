import logging
import asyncio
import json
import openai
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_models import Article
import time

class ArticleTranslator:
    def __init__(self):
        # 数据库配置
        self.db_url = "你的数据库链接"
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # OpenAI配置
        openai.api_key = ""
        openai.base_url = "https://api.gpt.ge/v1/"
        
        # 日志配置
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def get_untranslated_articles(self, limit=3):
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
            logging.error(f"更新翻译错误：{str(e)}")
            return False
        finally:
            session.close()

    async def translate_text(self, title: str, summary: str, max_retries: int = 3):
        """翻译文本"""
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
                
                # 使用同步方法替代异步方法
                completion = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=2000
                )
                
                response = completion.choices[0].message.content
                translation = json.loads(response)
                
                if translation['title'].strip() and translation['abstract'].strip():
                    logging.info(f"翻译成功 (尝试 {attempt + 1}/{max_retries})")
                    return translation['title'], translation['abstract']
                else:
                    raise ValueError("翻译结果为空")
                    
            except Exception as e:
                logging.error(f"翻译失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)  # 增加等待时间到5秒
                    continue
                    
        return None, None

    async def translate_single_article(self, article):
        """翻译单篇文章"""
        try:
            logging.info(f"开始翻译文章 ID {article.id}: {article.title[:50]}...")
            
            # 翻译文章
            title_zh, summary_zh = await self.translate_text(
                article.title,
                article.summary
            )
            
            # 更新翻译结果
            if title_zh and summary_zh:
                self.update_article_translation(
                    article.id,
                    title_zh,
                    summary_zh
                )
                logging.info(f"文章 ID {article.id} 翻译成功")
            else:
                logging.warning(f"文章 ID {article.id} 翻译失败")
                
            # 每篇文章翻译后等待10秒
            await asyncio.sleep(10)
                
        except Exception as e:
            logging.error(f"处理文章 {article.id} 时出错: {str(e)}")

    async def translate_batch(self, articles):
        """并行翻译一批文章"""
        tasks = []
        for article in articles:
            task = asyncio.create_task(self.translate_single_article(article))
            tasks.append(task)
        
        await asyncio.gather(*tasks)

    async def run(self):
        """运行翻译程序"""
        logging.info("开始翻译未翻译的文章...")
        
        while True:
            # 获取一批未翻译的文章
            articles = self.get_untranslated_articles(limit=10)
            if not articles:
                logging.info("没有找到未翻译的文章")
                break
            
            # 并行翻译这一批文章
            await self.translate_batch(articles)
            
            # 每批文章之间等待30秒
            await asyncio.sleep(30)
            
        logging.info("所有文章翻译完成")

async def main():
    translator = ArticleTranslator()
    await translator.run()

if __name__ == "__main__":
    asyncio.run(main()) 