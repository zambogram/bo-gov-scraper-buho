#!/usr/bin/env python3
"""
Daily Scheduler for BÚHO Scraper
Runs automatic scraping and syncing tasks
"""
import sys
import os
import time
import json
import schedule
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import get_scraper, SCRAPERS
from scraper.parser import LegalParser


def run_daily_scraping():
    """Run daily scraping task"""
    print(f"\n{'='*60}")
    print(f"Starting daily scraping: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    # Create log directory
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'auto')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    results = {
        'timestamp': datetime.now().isoformat(),
        'sites': {},
        'totals': {
            'new': 0,
            'modified': 0,
            'unchanged': 0,
            'errors': 0,
            'total_articles': 0
        }
    }

    # Scrape all sites
    for site_name in SCRAPERS.keys():
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scraping {site_name}...")

        try:
            scraper = get_scraper(site_name)

            # Scrape with only_new flag
            stats = scraper.scrape(limit=50, only_new=True)

            # Parse articles
            documents = scraper.load_index()
            articles = LegalParser.parse_all_documents(documents)
            scraper.save_articles(articles)

            # Export JSONL
            export_result = scraper.export_jsonl()

            # Update results
            results['sites'][site_name] = {
                'scraping': stats,
                'articles_parsed': len(articles),
                'exported': export_result
            }

            # Update totals
            for key in ['new', 'modified', 'unchanged', 'errors']:
                results['totals'][key] += stats.get(key, 0)
            results['totals']['total_articles'] += len(articles)

            print(f"  ✓ New: {stats['new']}, Modified: {stats['modified']}, Articles: {len(articles)}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results['sites'][site_name] = {
                'error': str(e)
            }
            results['totals']['errors'] += 1

    # Try to sync with Supabase
    try:
        from sync.supabase_sync import sync_all_sites

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Syncing to Supabase...")
        sync_results = sync_all_sites(only_new=True)
        results['supabase_sync'] = sync_results
        print("  ✓ Supabase sync complete")

    except Exception as e:
        print(f"  ⚠ Supabase sync skipped: {e}")
        results['supabase_sync'] = {
            'skipped': True,
            'reason': str(e)
        }

    # Save log
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print("Daily scraping complete!")
    print(f"Total New: {results['totals']['new']}")
    print(f"Total Modified: {results['totals']['modified']}")
    print(f"Total Articles: {results['totals']['total_articles']}")
    print(f"Log saved: {log_file}")
    print(f"{'='*60}\n")


def run_scheduler():
    """Run the scheduler"""
    print("🦉 BÚHO Daily Scheduler Started")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nScheduled tasks:")
    print("  - Daily scraping: 02:00 AM")
    print("\nPress Ctrl+C to stop\n")

    # Schedule daily scraping at 2 AM
    schedule.every().day.at("02:00").do(run_daily_scraping)

    # For testing: uncomment to run every 5 minutes
    # schedule.every(5).minutes.do(run_daily_scraping)

    # Run immediately on start (optional)
    # run_daily_scraping()

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='BÚHO Daily Scheduler')
    parser.add_argument('--now', action='store_true', help='Run scraping immediately')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')

    args = parser.parse_args()

    if args.now:
        # Run immediately
        run_daily_scraping()
    elif args.daemon:
        # Run as daemon
        run_scheduler()
    else:
        # Default: show help
        print("BÚHO Daily Scheduler")
        print("\nUsage:")
        print("  python scheduler/run_daily.py --now      Run scraping immediately")
        print("  python scheduler/run_daily.py --daemon   Run as background scheduler")
        print("\nExample:")
        print("  python scheduler/run_daily.py --now")
