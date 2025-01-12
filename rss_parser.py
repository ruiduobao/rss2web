import feedparser
import datetime
from typing import Dict, List
from db_operations import DatabaseManager
from db_models import Journal, Article

class RemoteSensingRSSParser:
    def __init__(self):
        # Remote Sensing journal RSS feed URL
        self.rss_url = "https://www.mdpi.com/rss/journal/remotesensing"
        
    def fetch_latest_papers(self, limit: int = 10) -> List[Dict]:
        """
        Fetch the latest papers from Remote Sensing journal RSS feed
        
        Args:
            limit (int): Maximum number of papers to return
            
        Returns:
            List[Dict]: List of papers with their details
        """
        try:
            # Parse the RSS feed
            feed = feedparser.parse(self.rss_url)
            
            papers = []
            for entry in feed.entries[:limit]:
                paper = {
                    'title': entry.title,
                    'authors': entry.get('authors', []),
                    'link': entry.link,
                    'published': entry.published,
                    'summary': entry.summary,
                    'doi': entry.get('prism_doi', '')
                }
                papers.append(paper)
                
            return papers
            
        except Exception as e:
            print(f"Error fetching RSS feed: {str(e)}")
            return []
            
    def print_papers(self, papers: List[Dict]):
        """
        Print papers in a formatted way
        
        Args:
            papers (List[Dict]): List of paper dictionaries
        """
        for i, paper in enumerate(papers, 1):
            print(f"\n=== Paper {i} ===")
            print(f"Title: {paper['title']}")
            print(f"Authors: {', '.join(str(author) for author in paper['authors'])}")
            print(f"Published: {paper['published']}")
            print(f"DOI: {paper['doi']}")
            print(f"Link: {paper['link']}")
            print("Summary:", paper['summary'][:20000] + "..." if len(paper['summary']) > 20000 else paper['summary'])
            print("="*50)

def main():
    # 初始化数据库管理器
    db_manager = DatabaseManager()
    db_manager.init_db()
    
    # 添加Remote Sensing期刊
    journal_id = db_manager.add_journal(
        name="Remote Sensing",
        rss_url="https://www.mdpi.com/rss/journal/remotesensing",
        description="MDPI Remote Sensing Journal"
    )
    
    # 获取并存储文章
    parser = RemoteSensingRSSParser()
    papers = parser.fetch_latest_papers(limit=500)
    
    if papers:
        print(f"\nFound {len(papers)} latest papers from Remote Sensing journal:")
        for paper in papers:
            article_id = db_manager.add_article(journal_id, paper)
            if article_id:
                print(f"Added article: {paper['title']}")
            else:
                print(f"Article already exists: {paper['title']}")
    else:
        print("No papers found or error occurred while fetching the RSS feed.")

if __name__ == "__main__":
    main()

