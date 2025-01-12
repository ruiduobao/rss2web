import feedparser
from db_operations import DatabaseManager
import logging
from datetime import datetime
import time

class RSSManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def parse_title(self, title):
        """解析标题，提取卷号和页码"""
        volume = ''
        pages = ''
        actual_title = title
        
        # 尝试提取卷号和页码
        if ', Vol.' in title and ', Pages' in title:
            try:
                parts = title.split(', ')
                journal_name = parts[0]
                
                for part in parts:
                    if 'Vol.' in part:
                        volume = part.split('Vol.')[1].strip()
                    elif 'Pages' in part:
                        # 只取页码数字部分
                        pages = part.split('Pages')[1].split(':')[0].strip()
                
                # 获取实际标题（冒号后的部分）
                if ': ' in title:
                    actual_title = title.split(': ', 1)[1]
            except:
                pass  # 如果解析失败，使用原始标题
                
        return {
            'volume': volume,
            'pages': pages,
            'actual_title': actual_title
        }

    def update_all_journals(self):
        """更新所有期刊"""
        logging.info("Starting RSS update cycle...")
        
        urls = self.load_rss_urls('rss.txt')
        if not urls:
            logging.error("No RSS URLs found in file")
            return
            
        for url in urls:
            try:
                logging.info(f"Processing URL: {url}")
                journal_name = self.get_journal_name_from_url(url)
                journal_id = self.db_manager.get_or_create_journal(
                    name=journal_name,
                    rss_url=url
                )
                
                feed = feedparser.parse(url)
                if hasattr(feed, 'status') and feed.status != 200:
                    logging.error(f"Failed to fetch feed. Status: {feed.status}")
                    continue
                    
                logging.info(f"Found {len(feed.entries)} entries in feed")
                new_articles = 0
                
                for entry in feed.entries:
                    try:
                        # 解析标题
                        title_info = self.parse_title(entry.title)
                        
                        # 获取摘要
                        summary = entry.get('summary', '') or entry.get('description', '')
                        
                        # 解析文章数据
                        article_data = {
                            'title': title_info['actual_title'],  # 使用实际标题
                            'authors': entry.get('authors', []),
                            'link': entry.link,
                            'published': entry.get('published', datetime.now().strftime('%Y-%m-%d')),
                            'summary': summary,
                            'doi': entry.get('prism_doi', '') or entry.get('id', ''),
                            'volume': title_info['volume'],
                            'pages': title_info['pages'],
                            'journal_id': journal_id
                        }
                        
                        # 添加原始文章（不包含翻译）
                        article_id = self.db_manager.add_article_without_translation(article_data)
                        if article_id:
                            new_articles += 1
                            logging.info(f"Added article: {entry.title[:50]}...")
                        
                    except Exception as e:
                        logging.error(f"Error processing article: {str(e)}")
                        continue
                
                logging.info(f"Journal {journal_name}: Added {new_articles} new articles")
                
            except Exception as e:
                logging.error(f"Error processing journal {url}: {str(e)}")
                continue

    def load_rss_urls(self, filename):
        try:
            with open(filename, 'r') as f:
                urls = [line.strip().rstrip(';') for line in f if line.strip()]
                logging.info(f"Loaded {len(urls)} URLs from {filename}")
                return urls
        except Exception as e:
            logging.error(f"Error loading RSS URLs: {str(e)}")
            return []

    @staticmethod
    def get_journal_name_from_url(url):
        name = url.split('/')[-1].split('.')[0].capitalize()
        return name

def main():
    rss_manager = RSSManager()
    rss_manager.update_all_journals()

if __name__ == "__main__":
    main()