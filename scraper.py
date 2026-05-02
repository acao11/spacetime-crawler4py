import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from collections import Counter
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
    try:
        parsed = urlparse(url)
        # 1. Basic Protocol & Domain Checks
        if parsed.scheme not in set(["http", "https"]):
            return False
<<<<<<< HEAD
        #Domain check
        if parsed.netloc not in Allowed_Domains:
=======
        if not any(parsed.netloc == d or parsed.netloc.endswith('.' + d) for d in Allowed_Domains):
>>>>>>> 864fb57 (fixed some checks,)
            return False
            
        # 2. Low Information Value Families
        # mailman contains thousands of email list pages with very little unique content
        if "mailman.ics.uci.edu" in parsed.netloc.lower():
            return False

        path_lower = parsed.path.lower()
        # 3. Extension check (Block non-HTML files)
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|ipynb"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
            + r"|war|conf|sql|java|php|py|c|cpp|h|sh|mpg)$", path_lower):
            return False

        # 4. Structural Traps (Proactive Heuristics)
        path_segments = [seg for seg in path_lower.split('/') if seg]
        query_parts = [p for p in parsed.query.lower().split('&') if p]
        
        # a) Depth Limit: Paths that are too deep (more than 10 levels) are usually traps
        if len(path_segments) > 10:
            return False

        # b) Query Complexity: URLs with too many params are usually dynamic traps
        if len(query_parts) > 3:
            return False

        # c) Repeating Directory Pattern (e.g., /news/news/news/)
        if len(path_segments) > 0:
            counts = Counter(path_segments)
            if any(count > 2 for count in counts.values()):
                return False

        # 5. Targeted Traps (Reactive Rules)
        # a) Wiki & Utility Traps
        traps = [
            "/attachment/", "/browser/", "/timeline", "/action/", "/login", "/logout", 
            "/auth", "/signup", "/password", "/helpdesk", "/swiki", "/gitlab"
        ]
        if any(trap in path_lower for trap in traps):
            return False

        # b) Known Trap Parameters (Wiki versions, Sorting, Filters)
        trap_params = {
            "tribe-bar-date", "eventdisplay", "outlook-ical", "share", "replytocom", 
            "afg", "ical", "from", "version", "format", "rev", "C", "O", "M", "S", 
            "P", "sort", "order", "filter"
        }
        for part in query_parts:
            param_name = part.split('=')[0]
            if param_name in trap_params:
                return False

        # c) Dynamic Event/Calendar Paths (Stop infinite date loops)
        if any(x in path_lower for x in ["/events/", "/calendar/", "/schedule/"]):
            if any(x in path_lower for x in ["/day/", "/list/", "/month/", "/week/"]) or re.search(r'/\d{4}-\d{2}', path_lower):
                return False

        # 6. Pagination Trap Check (Limit to 50 pages)
        # Check path (e.g., /page/194)
        page_match = re.search(r'/page/(\d+)', path_lower)
        if page_match and int(page_match.group(1)) > 50:
            return False
        
        # Check query (e.g., ?page=205, ?p=205)
        for part in query_parts:
            match = re.search(r'^(?:page|p)=(\d+)', part)
            if match and int(match.group(1)) > 50:
                return False

        # 7. Final Path Length Check
        if len(url) > 200:
            return False

        return True
    except TypeError:
        print ("TypeError for ", parsed)
        raise
