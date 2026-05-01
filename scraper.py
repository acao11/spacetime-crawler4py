import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

Allowed_Domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    if resp.status != 200 or resp.raw_response is None:
        return []
    try:
        soup = BeautifulSoup(resp.raw_response.content, "lxml")
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
        if not any(parsed.netloc == d or parsed.netloc.endswith('.' + d) for d in Allowed_Domains):
            return False
        #Extension check
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
            + r"|war|conf|sql|java|php|py|c|cpp|h|sh|ical)$", parsed.path.lower()):
            return False

        # --- Crawler Trap Check ---

        # 1. Wiki/Trac Specific Traps (like grape.ics.uci.edu)
        # /attachment/ contains junk files (WAR, CONF, etc.)
        # /browser/ is an infinite source code browser
        # /timeline/ is an infinite history list
        # We also block common auth/login paths to avoid getting stuck on login screens. 
        if any(trap in parsed.path.lower() for trap in [
            "/attachment/", "/browser/", "/timeline/", "/action/", "/login", "/logout", "/auth", 
            "/signup", "doku.php", "/zip-attachment/", "/raw-attachment/", "wp-admin", "wp-login"
        ]):
            return False
        
        # Calendar URL trap
        if re.search(r"/day/\d{4}-\d{2}-\d{2}", parsed.path.lower()):
            return False

        if re.search(r"/\d{4}-\d{2}(/|$)", parsed.path.lower()):
            return False

        # 2. Repeating Directory Pattern
        # Some traps look like /news/news/news/news/... 
        # We split the path by '/' and check if any folder name appears more than twice.
        path_segments = [seg for seg in parsed.path.split('/') if seg]
        if len(path_segments) > 0:
            from collections import Counter
            counts = Counter(path_segments)
            if any(count > 2 for count in counts.values()):
                return False

        # 3. Dangerous Query Parameters (Wiki/Calendar Traps)
        # These parameters often create infinite variations of the same content.
        # 'do' (wiki actions), 'rev' (history), 'replytocom' (comment loops)
        # 'idx' is a DokuWiki index trap.
        trap_params = {"do", "rev", "action", "share", "replytocom", "diff", "afg", "ical", "idx", "c", "o"}
        query_parts = parsed.query.lower().split('&')
        for part in query_parts:
            param_name = part.split('=')[0]
            if param_name in trap_params:
                return False

        # 4. Path Length Heuristic
        # Extremely long paths are rarely legitimate content and often signify a trap.
        if len(url) > 200:
            return False

        return True
    except TypeError:
        print ("TypeError for ", parsed)
        raise
