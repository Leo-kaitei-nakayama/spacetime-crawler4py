import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from PartA import tokenize, computeWordFrequencies, print_freq
import atexit
from hashlib import md5

unique_pages = set()
word_frequency = {}
longest_page = {"url": "", "count": 0}
sub_domain_page = {}
page_fingerprints = set()
url_path_counts = {}
crawled_count = {} 
atexit.register(print_report)


STOP_WORDS = {
    "a","about","above","after","again","against","all","am","an","and","any",
    "are","as","at","be","because","been","before","being","below","between",
    "both","but","by","cannot","could","did","do","does","doing","down",
    "during","each","few","for","from","further","get","had","has","have",
    "having","he","her","here","hers","herself","him","himself","his","how",
    "i","if","in","into","is","it","its","itself","me","more","most","my",
    "myself","no","nor","not","of","off","on","once","only","or","other",
    "our","ours","ourselves","out","over","own","same","she","should","so",
    "some","such","than","that","the","their","theirs","them","themselves",
    "then","there","these","they","this","those","through","to","too","under",
    "until","up","very","was","we","were","what","when","where","which",
    "while","who","whom","why","will","with","would","you","your","yours",
    "yourself","yourselves"
}

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    
    # This check that url is not an empty, and it has to be string
    if not url or not isinstance(url, str): 
        return []
    
    # check that resp exist
    if resp is None:
        return []
    
    # make sure the http is 200 to process
    if resp.status != 200:
        return []
    
    if resp.raw_response is None:
        return []
    if not resp.raw_response.content:
        return []
    
    #This get the type of data server sent back
    content_type = resp.raw_response.headers.get("Content-Type", "")
    #the content must be the html form
    if "text/html" not in content_type:
        return []
    
    #TODO: This size is what I think will be reasonable for the oversize page
    if len(resp.raw_response.content) > 5 * 1024 * 1024:
        return []
    
    try:
        soup = BeautifulSoup(resp.raw_response.content, 'lxml')
    except Exception as e:
        print(f"BeautifulSoup parse error for {url}: {e}")
        return []
    
    for tag in soup(["script", "style", "header", "footer", "nav", "meta"]):
        tag.decompose()
        
    try:
        defragged_url, _ = urldefrag(url)
    except Exception:
        return []
    
    
    #Tokenizer from pervious assignment comes here
    text = soup.get_text(separator=" ")
    tokens = tokenize(text)
    filtered = [t.lower() for t in tokens if t.lower() not in STOP_WORDS]
    
    if len(filtered) < 50:
        return []
    
    #do the near-duplicate fingerprints
    try: 
        words = md5(" ".join(sorted(set(filtered))).encode())
        frequency = words.hexdigest()
    except Exception:
        frequency = None
       
    #Check if frecuency exist but is not same with one in page-fingerprints.  
    if frequency is not None:
        if frequency in page_fingerprints:
            return []
        page_fingerprints.add(frequency)
    
    #TODO: this is analysis part but not clear so figure out this part   
    if defragged_url not in unique_pages:
        unique_pages.add(defragged_url)
        
        page_freq = computeWordFrequencies(filtered)
        for word, count in page_freq.items():
            if word in word_frequency:
                word_frequency[word] += count
            else:
                word_frequency[word] = count
        
        raw_count = len(tokens)   
        if raw_count > longest_page["count"]:
            longest_page["url"] = defragged_url
            longest_page["count"] = raw_count
            
        try:
            host = urlparse(defragged_url).netloc.lower().split(":")[0]
        except Exception:
            host = ""
            
        if host:
            if host in crawled_count:
                crawled_count[host] += 1
            else:
                crawled_count[host] = 1
                
            if host.endswith(".uci.edu"):
                if host in sub_domain_page:
                    sub_domain_page[host].add(defragged_url)
                else:
                    sub_domain_page[host] = {defragged_url}
    
    #Extract link         
    extracted = []
    for tag1 in soup.find_all('a', href=True):
        href = tag1["href"]
        
        #check that href is non-empty String
        if not href or not isinstance(href, str):
            continue
        
        href = href.strip()
        if not href:
            continue
        
        # skip not https
        if href.startswith(("mailto:", "javascript:", "tel:", "#", "ftp:")):
            continue
        
        try:
            absolute = urljoin(url, href)
            defragged, _ = urldefrag(absolute)
            if defragged:
                extracted.append(defragged)
        except Exception as e:
            print(f"URL join error for href '{href}' on page {url}: {e}")
            continue
        
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    return extracted

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        if not url or not isinstance(url, str):
            return False
        
        parsed = urlparse(url)
        
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        if not parsed.netloc:
            return False
        
        host = parsed.netloc.lower().split(":")[0]
        if not re.match(r"^([\w\-]+\.)*(ics|cs|informatics|stat)\.uci\.edu$", host):
            return False
        
        path = parsed.path.lower()
        if re.search(r"\.(sql|db|log|xml|json|rss|atom|txt|tsv|apk|py|r|mat)$", path):
            return False
        
        path_parts = [p for p in path.split("/") if p]
        if len(path_parts) > 4 and len(path_parts) != len(set(path_parts)):
            return False
        
        if parsed.query.count("&") > 3:
            return False
        
        if re.search(
            r"(calendar|/event/|/tag/|/category/"
            r"|replytocom|format=rss|feed=rss"
            r"|phpsessid|sid=|action=login|action=edit"
            r"|diff=|oldid=|offset=|sort=|order=|filter=)",
            url.lower()
        ):
            return False
        
        if detect_trap(url):
            return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise


def detect_trap(url):
    """ This function return true when the url looks like the crawler trap"""
    if not url or not isinstance(url, str):
        return True
    
    try:
        parsed = urlparse(url)
    except Exception:
        return True
    
    host = parsed.netloc.lower().split(":")[0]
    path = parsed.path.lower()
    query = parsed.query.lower()
    
    # # First trap detection
    # if host in crawled_count and crawled_count[host] > 500:
    #     return True
    
    # Too many URLs under the same path prefix
    path_parts = [p for p in path.split("/") if p]
    if len(path_parts) >= 2:
        path_prefix = host + "/" + "/".join(path_parts[:2])
    else:
        path_prefix = host + "/" + path
        
    if path_prefix:
        if path_prefix in url_path_counts:
            url_path_counts[path_prefix] += 1
        else:
            url_path_counts[path_prefix] = 1
        if url_path_counts[path_prefix] > 200:
            return True
    
    # Long numeric segment
    if re.search(r"/\d{4,}", path):
        return True
    
    if re.search(r"(year|month|day|date)=\d+", query):
        return True
    
    if len(url) > 200:
        return True
    
    if re.search(r"(/[^/]+)\1{2,}", path):
        return True
    
    if len(path_parts) > 8:
        return True
    
    return False
    

def get_count(item):
    return -item[1]

def print_report():
    print("-----REPORT-----")
    print(f"1. Unique pages: {len(unique_pages)}")
    print(f"2. Longest page: {longest_page['url']} ({longest_page['count']} words)")
    print(f"3. Top 50 words:")
    top_50 = dict(sorted(word_frequency.items(), key=get_count)[:50])
    print_freq(top_50)
    print(f"4. Subdomains ({len(sub_domain_page)} total):")
    sub_lst = sorted(sub_domain_page.keys())
    for sub in sub_lst:
        print(f"   {sub}, {len(sub_domain_page[sub])}")
            