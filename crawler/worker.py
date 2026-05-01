from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
from urllib.parse import urlparse

from utils.stats import tracker

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.download_count = 0  # Track downloads for this worker
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            
            # Domain-Specific Politeness Logic
            parsed = urlparse(tbd_url)
            domain = parsed.netloc
            
            # Use the frontier's lock to coordinate domain access
            with self.frontier.lock:
                if not hasattr(self.frontier, 'last_visit'):
                    self.frontier.last_visit = {}
                
                last_time = self.frontier.last_visit.get(domain, 0)
                curr_time = time.time()
                time_since_last = curr_time - last_time
                
                wait_time = 0
                if time_since_last < self.config.time_delay:
                    wait_time = self.config.time_delay - time_since_last
                
                # Update last visit time (assuming we will download it now)
                # We add the wait time to the current time to "reserve" the next slot
                self.frontier.last_visit[domain] = curr_time + wait_time

            if wait_time > 0:
                time.sleep(wait_time)

            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)

            # Periodically save report (every 50 downloads per worker)
            self.download_count += 1
            if self.download_count % 50 == 0:
                tracker.save_report("report.txt")
                self.logger.info(f"Worker-{self.name.split('-')[-1]} updated report.txt")
