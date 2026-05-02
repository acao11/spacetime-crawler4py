import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from utils.stats import tracker
from utils.tokenizer import tokenize

Allowed_Domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    if resp.status != 200 or resp.raw_response is None:
        return []
    try:
        content = resp.raw_response.content
        soup = BeautifulSoup(content, "lxml")
        
        # --- Update Stats ---
        text = soup.get_text()
        tokens = tokenize(text)
        tracker.update_stats(url, tokens)

        # --- Content-Aware Filtering (Trap Detection) ---
        # 1. Skip links from massive pages with very little text (e.g., big data files)
        if len(content) > 1_000_000 and len(tokens) < 200:
            return []
        
        # 2. Skip links from repetitive traps (Long pages with low unique word ratio)
        if len(tokens) > 2000:
            unique_ratio = len(set(tokens)) / len(tokens)
            if unique_ratio < 0.1: # Less than 10% unique words
                return []

        # --- Extract Links ---
        links = []
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            absolute = urljoin(url, href)
            absolute = absolute.split("#")[0]
            if absolute:
                links.append(absolute)
        return links
    except Exception as e:
        print(f"Error parsing {url}: {e}")  
        return []

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        #Http check
        if parsed.scheme not in set(["http", "https"]):
            return False
        #Domain check
        if parsed.netloc not in Allowed_Domains:
            return False
        #Extension check
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|ipynb"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
            + r"|war|conf|sql|java|php|py|c|cpp|h|sh|mpg)$", parsed.path.lower()):
            return False

        # Crawler Trap Check

        # Wiki Trap - More robust check
        path_lower = parsed.path.lower()
        traps = ["/attachment/", "/browser/", "/timeline", "/action/", "/login", "/logout", "/auth", "/signup"]
        if any(trap in path_lower for trap in traps):
            return False

        #  Repeating Directory Pattern
        #/news/news/news/news/

        path_segments = [seg for seg in parsed.path.split('/') if seg]
        if len(path_segments) > 0:
            from collections import Counter
            counts = Counter(path_segments)
            if any(count > 2 for count in counts.values()):
                return False

        # 2.Wiki/Calendar/Sorting Traps
     
        trap_params = {
            "do", "rev", "action", "share", "replytocom", "diff", "afg", "ical", 
            "idx", "from", "c", "o", "tribe-bar-date", "eventdisplay", "outlook-ical"
        }
        query_parts = parsed.query.lower().split('&')
        for part in query_parts:
            param_name = part.split('=')[0]
            if param_name in trap_params:
                return False

        # 3. Dynamic Event/Calendar Path Traps
        if "/events/" in path_lower and any(x in path_lower for x in ["/day/", "/list/"]):
            return False

        # 4. Path Length Check

        if len(url) > 200:
            return False

        # 4. Pagination Trap Check (Limit to 50 pages)
        # Check path (e.g., /page/194)
        page_match = re.search(r'/page/(\d+)', path_lower)
        if page_match:
            if int(page_match.group(1)) > 50:
                return False
        
        # Check query (e.g., ?page=205, ?p=205)
        for part in query_parts:
            match = re.search(r'^(?:page|p)=(\d+)', part)
            if match:
                if int(match.group(1)) > 50:
                    return False

        return True
    except TypeError:
        print ("TypeError for ", parsed)
        raise
