"""
Supabase synchronization module for BÚHO scraper
Handles syncing documents and articles to Supabase database
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: supabase-py not installed. Install with: pip install supabase")


class SupabaseSync:
    """Supabase synchronization handler"""

    def __init__(self):
        if not SUPABASE_AVAILABLE:
            raise ImportError("supabase-py is not installed")

        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment or .env file"
            )

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

        # Create logs directory
        self.logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'sync')
        os.makedirs(self.logs_dir, exist_ok=True)

    def sync_documents(self, documents: List[Dict], site: str) -> Dict:
        """
        Sync documents to Supabase

        Args:
            documents: List of document dictionaries
            site: Site name (tcp, tsj, etc.)

        Returns:
            Dict with sync statistics
        """
        stats = {
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'site': site,
            'timestamp': datetime.now().isoformat()
        }

        for doc in documents:
            try:
                # Check if document exists by MD5
                existing = self.client.table('documents').select('id, md5').eq('md5', doc['md5']).execute()

                if existing.data:
                    # Document exists - check if modified
                    if existing.data[0]['md5'] == doc['md5']:
                        stats['skipped'] += 1
                    else:
                        # Update modified document
                        self.client.table('documents').update({
                            'title': doc['title'],
                            'content': doc['content'],
                            'md5': doc['md5'],
                            'metadata': doc.get('metadata', {}),
                            'updated_at': datetime.now().isoformat()
                        }).eq('id', existing.data[0]['id']).execute()
                        stats['updated'] += 1
                else:
                    # Insert new document
                    self.client.table('documents').insert({
                        'id': doc['id'],
                        'site': doc['site'],
                        'url': doc['url'],
                        'title': doc['title'],
                        'content': doc['content'],
                        'md5': doc['md5'],
                        'metadata': doc.get('metadata', {}),
                        'scraped_at': doc.get('scraped_at'),
                        'created_at': datetime.now().isoformat()
                    }).execute()
                    stats['inserted'] += 1

            except Exception as e:
                print(f"Error syncing document {doc.get('id')}: {e}")
                stats['errors'] += 1

        return stats

    def sync_articles(self, articles: List[Dict], site: str) -> Dict:
        """
        Sync articles to Supabase

        Args:
            articles: List of article dictionaries
            site: Site name

        Returns:
            Dict with sync statistics
        """
        stats = {
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'site': site,
            'timestamp': datetime.now().isoformat()
        }

        for article in articles:
            try:
                # Check if article exists
                existing = self.client.table('articles').select('id').eq('id', article['id']).execute()

                if existing.data:
                    # Update existing article
                    self.client.table('articles').update({
                        'content': article['content'],
                        'metadata': article.get('metadata', {}),
                        'updated_at': datetime.now().isoformat()
                    }).eq('id', article['id']).execute()
                    stats['updated'] += 1
                else:
                    # Insert new article
                    self.client.table('articles').insert({
                        'id': article['id'],
                        'document_id': article['document_id'],
                        'site': article['site'],
                        'article_number': article['article_number'],
                        'content': article['content'],
                        'metadata': article.get('metadata', {}),
                        'created_at': datetime.now().isoformat()
                    }).execute()
                    stats['inserted'] += 1

            except Exception as e:
                print(f"Error syncing article {article.get('id')}: {e}")
                stats['errors'] += 1

        return stats

    def verify_duplicates(self, site: Optional[str] = None) -> List[Dict]:
        """
        Verify duplicates in database

        Args:
            site: Optional site filter

        Returns:
            List of duplicate entries
        """
        query = self.client.table('documents').select('md5, count')

        if site:
            query = query.eq('site', site)

        # Group by MD5 and count
        # Note: This is a simplified version. In practice, you'd use SQL aggregation
        result = query.execute()

        # Find duplicates
        md5_counts = {}
        for doc in result.data:
            md5 = doc['md5']
            md5_counts[md5] = md5_counts.get(md5, 0) + 1

        duplicates = [
            {'md5': md5, 'count': count}
            for md5, count in md5_counts.items()
            if count > 1
        ]

        return duplicates

    def get_stats(self, site: Optional[str] = None) -> Dict:
        """
        Get statistics from Supabase

        Args:
            site: Optional site filter

        Returns:
            Dict with statistics
        """
        try:
            # Count documents
            doc_query = self.client.table('documents').select('*', count='exact')
            if site:
                doc_query = doc_query.eq('site', site)
            doc_result = doc_query.execute()

            # Count articles
            art_query = self.client.table('articles').select('*', count='exact')
            if site:
                art_query = art_query.eq('site', site)
            art_result = art_query.execute()

            return {
                'site': site or 'all',
                'total_documents': len(doc_result.data) if doc_result.data else 0,
                'total_articles': len(art_result.data) if art_result.data else 0,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                'site': site or 'all',
                'total_documents': 0,
                'total_articles': 0,
                'error': str(e)
            }

    def log_sync_results(self, stats: Dict):
        """
        Log sync results to file

        Args:
            stats: Statistics dictionary
        """
        log_file = os.path.join(
            self.logs_dir,
            f"sync_{stats['site']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print(f"Sync log saved to: {log_file}")


# Public API functions

def sync_documents_to_supabase(site: str, only_new: bool = False) -> Dict:
    """
    Sync documents from a site to Supabase

    Args:
        site: Site name (tcp, tsj, etc.)
        only_new: Only sync new documents

    Returns:
        Sync statistics
    """
    from scraper import get_scraper

    syncer = SupabaseSync()
    scraper = get_scraper(site)
    documents = scraper.load_index()

    if only_new:
        documents = [d for d in documents if d.get('status') == 'new']

    stats = syncer.sync_documents(documents, site)
    syncer.log_sync_results(stats)

    return stats


def sync_articles_to_supabase(site: str, only_new: bool = False) -> Dict:
    """
    Sync articles from a site to Supabase

    Args:
        site: Site name
        only_new: Only sync new articles

    Returns:
        Sync statistics
    """
    from scraper import get_scraper

    syncer = SupabaseSync()
    scraper = get_scraper(site)
    articles = scraper.load_articles()

    if only_new:
        # Filter based on document status
        documents = scraper.load_index()
        new_doc_ids = {d['id'] for d in documents if d.get('status') == 'new'}
        articles = [a for a in articles if a.get('document_id') in new_doc_ids]

    stats = syncer.sync_articles(articles, site)
    syncer.log_sync_results(stats)

    return stats


def sync_all_sites(only_new: bool = False) -> Dict:
    """
    Sync all sites to Supabase

    Args:
        only_new: Only sync new documents/articles

    Returns:
        Combined statistics
    """
    from scraper import SCRAPERS

    total_stats = {
        'documents': {'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
        'articles': {'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
        'sites': [],
        'timestamp': datetime.now().isoformat()
    }

    for site in SCRAPERS.keys():
        print(f"\nSyncing {site}...")

        # Sync documents
        doc_stats = sync_documents_to_supabase(site, only_new)
        for key in ['inserted', 'updated', 'skipped', 'errors']:
            total_stats['documents'][key] += doc_stats.get(key, 0)

        # Sync articles
        art_stats = sync_articles_to_supabase(site, only_new)
        for key in ['inserted', 'updated', 'skipped', 'errors']:
            total_stats['articles'][key] += art_stats.get(key, 0)

        total_stats['sites'].append({
            'site': site,
            'documents': doc_stats,
            'articles': art_stats
        })

    return total_stats


def verify_duplicates(site: Optional[str] = None) -> List[Dict]:
    """
    Verify duplicates in Supabase

    Args:
        site: Optional site filter

    Returns:
        List of duplicates
    """
    syncer = SupabaseSync()
    return syncer.verify_duplicates(site)


def log_sync_results(stats: Dict):
    """
    Log sync results

    Args:
        stats: Statistics dictionary
    """
    syncer = SupabaseSync()
    syncer.log_sync_results(stats)


def get_stats_from_supabase(site: Optional[str] = None) -> Dict:
    """
    Get statistics from Supabase

    Args:
        site: Optional site filter

    Returns:
        Statistics dictionary
    """
    syncer = SupabaseSync()
    return syncer.get_stats(site)
