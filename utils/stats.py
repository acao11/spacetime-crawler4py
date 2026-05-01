import threading
from collections import Counter
from urllib.parse import urlparse

class StatsTracker:
    def __init__(self):
        self.lock = threading.RLock()
        self.unique_pages = set()
        self.longest_page_url = ""
        self.longest_page_word_count = 0
        self.word_frequencies = Counter()
        self.subdomain_counts = Counter()

    def update_stats(self, url, tokens):
        with self.lock:
            # 1. Unique Pages
            self.unique_pages.add(url)

            # 2. Longest Page
            word_count = len(tokens)
            if word_count > self.longest_page_word_count:
                self.longest_page_word_count = word_count
                self.longest_page_url = url

            # 3. Word Frequencies
            self.word_frequencies.update(tokens)

            # 4. Subdomains of ics.uci.edu
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.endswith("ics.uci.edu") and domain != "www.ics.uci.edu":
                # Clean subdomain name (optional)
                self.subdomain_counts[domain] += 1

    def get_report(self):
        with self.lock:
            report = []
            report.append("--- CRAWLER REPORT ---")
            report.append(f"1. Unique pages: {len(self.unique_pages)}")
            report.append(f"2. Longest page: {self.longest_page_url} ({self.longest_page_word_count} words)")
            
            report.append("\n3. Top 50 words:")
            for word, count in self.word_frequencies.most_common(50):
                report.append(f"   {word}: {count}")
            
            report.append("\n4. Subdomains (ics.uci.edu):")
            for sub, count in sorted(self.subdomain_counts.items()):
                report.append(f"   {sub}, {count}")
            
            return "\n".join(report)

    def save_report(self, filename="report.txt"):
        with self.lock:
            content = self.get_report()
            with open(filename, "w") as f:
                f.write(content)

# Global singleton instance
tracker = StatsTracker()
