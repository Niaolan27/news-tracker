import threading
import time
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from supabase_database import SupabaseDatabase
from news_scraper import NewsScraper

logger = logging.getLogger(__name__)

class NewsScrapingScheduler:
    def __init__(self, database=None, scraper=None):
        """Initialize the scheduler with database and scraper instances"""
        self.db = database or SupabaseDatabase()
        self.scraper = scraper or NewsScraper(self.db)
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
    def scrape_job(self):
        """Job function that runs the scraping"""
        try:
            logger.info("Starting scheduled news scrape...")
            results = self.scraper.scrape_all_feeds()
            
            total_new = sum(results.values())
            logger.info(f"Scheduled scrape completed: {total_new} new articles added")
            
            # Log individual feed results
            for feed_name, count in results.items():
                if count > 0:
                    logger.info(f"  {feed_name}: {count} new articles")
                    
        except Exception as e:
            logger.error(f"Error during scheduled scrape: {e}")
    
    def start_scheduler(self):
        """Start the periodic news scraping"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        # Add job to run every 2 hours
        self.scheduler.add_job(
            self.scrape_job,
            IntervalTrigger(hours=2),
            id='news_scraping_job',
            name='News Scraping Job',
            replace_existing=True
        )
        
        # Run an initial scrape immediately
        self.scheduler.add_job(
            self.scrape_job,
            'date',
            id='initial_scrape',
            name='Initial News Scrape'
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("News scraping scheduler started - will run every 2 hours")
        
    def stop_scheduler(self):
        """Stop the periodic news scraping"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
            
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("News scraping scheduler stopped")
        
    def get_next_run_time(self):
        """Get the next scheduled run time"""
        job = self.scheduler.get_job('news_scraping_job')
        if job:
            return job.next_run_time
        return None
        
    def get_scheduler_status(self):
        """Get current scheduler status"""
        return {
            'is_running': self.is_running,
            'next_run_time': self.get_next_run_time(),
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time
                }
                for job in self.scheduler.get_jobs()
            ]
        }

# Global scheduler instance
_scheduler_instance = None

def get_scheduler():
    """Get or create the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = NewsScrapingScheduler()
    return _scheduler_instance

def start_background_scraping():
    """Start background news scraping"""
    scheduler = get_scheduler()
    scheduler.start_scheduler()
    return scheduler

def stop_background_scraping():
    """Stop background news scraping"""
    scheduler = get_scheduler()
    scheduler.stop_scheduler()

if __name__ == "__main__":
    # Test the scheduler
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\nStopping scheduler...")
        stop_background_scraping()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting news scraping scheduler...")
    scheduler = start_background_scraping()
    
    print("Scheduler started. Press Ctrl+C to stop.")
    print(f"Next scrape: {scheduler.get_next_run_time()}")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_background_scraping()