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

        # Content-Aware Trap Check
        if len(content) > 1_000_000 and len(tokens) < 200:
            return []
        
        # Repetitive Content Trap
        if len(tokens) > 2000:
            unique_ratio = len(set(tokens)) / len(tokens)
            if unique_ratio < 0.1:
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
        # Basic Protocol & Domain Check
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not any(parsed.netloc == d or parsed.netloc.endswith('.' + d) for d in Allowed_Domains):
            return False
            
        # Low Information Value Check
        if "mailman.ics.uci.edu" in parsed.netloc.lower():
            return False

        path_lower = parsed.path.lower()
        # Extension Trap Check
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|ipynb"
            + r"|thmx|mso|arff|rtf|jar|csv|txt"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
            + r"|war|conf|sql|java|php|py|c|cpp|h|sh|mpg)$", path_lower):
            return False

        # Structural Trap Checks
        path_segments = [seg for seg in path_lower.split('/') if seg]
        query_parts = [p for p in parsed.query.lower().split('&') if p]
        
        # Depth Limit Trap
        if len(path_segments) > 10:
            return False

        # Query Complexity Trap
        if len(query_parts) > 3:
            return False

        # Repeating Directory Trap
        if len(path_segments) > 0:
            counts = Counter(path_segments)
            if any(count > 2 for count in counts.values()):
                return False

        # Utility & Wiki Traps
        traps = [
            "attachment", "/browser/", "/timeline", "/action/", "/login", "/logout", 
            "/auth", "/signup", "/password", "/helpdesk", "/swiki", "/gitlab"
        ]
        if any(trap in path_lower for trap in traps):
            return False

        # Parameter/Sorting Trap
        trap_params = {
            "tribe-bar-date", "eventdisplay", "outlook-ical", "share", "replytocom", 
            "afg", "ical", "from", "version", "format", "rev", "C", "O", "M", "S", 
            "P", "sort", "order", "filter"
        }
        for part in query_parts:
            param_name = part.split('=')[0]
            if param_name in trap_params:
                return False

        # Calendar/Event Trap
        if any(x in path_lower for x in ["/events/", "/calendar/", "/schedule/"]):
            if any(x in path_lower for x in ["/day/", "/list/", "/month/", "/week/"]) or re.search(r'/\d{4}-\d{2}', path_lower):
                return False

        # Pagination Trap
        page_match = re.search(r'/page/(\d+)', path_lower)
        if page_match and int(page_match.group(1)) > 50:
            return False
        
        for part in query_parts:
            match = re.search(r'^(?:page|p)=(\d+)', part)
            if match and int(match.group(1)) > 50:
                return False

        # Path Length Trap
        if len(url) > 200:
            return False

        return True
    except TypeError:
        print ("TypeError for ", parsed)
        raise
