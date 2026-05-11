import os, requests, sys, re, time
from urllib.parse import urljoin

# This makes sure logs show up on GitHub immediately
def log(msg):
    print(msg)
    sys.stdout.flush()

def is_valid(path):
    if not path or any(x in path for x in ['javascript:', 'mailto:', 'data:', 'http']):
        return False
    # Must have a dot for a file extension
    return '.' in path.split('/')[-1]

def mirror(url, base_url, folder, visited, depth=0):
    # Stop if too deep or already seen to prevent infinite loops
    if depth > 10 or url in visited or not url.startswith(base_url):
        return
    visited.add(url)

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200: return

        # Determine path
        rel = url.replace(base_url, "").lstrip("/")
        if not rel or rel.endswith('/'): rel += "index.html"
        
        path = os.path.join(folder, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'wb') as f:
            f.write(res.content)
        log(f"DOWNLOADED: {rel}")

        # Scan text files for more links
        ctype = res.headers.get('Content-Type', '')
        if 'text' in ctype or 'json' in ctype or 'javascript' in ctype:
            # Find any string in quotes
            found = re.findall(r'["\']([^"\'\s<>]+)["\']', res.text)
            for item in set(found):
                if is_valid(item):
                    # Remove version tags like ?v=1
                    clean_item = item.split('?')[0].split('#')[0]
                    full_url = urljoin(url, clean_item)
                    mirror(full_url, base_url, folder, visited, depth + 1)
                    
    except Exception as e:
        log(f"ERROR on {url}: {e}")

if __name__ == "__main__":
    target_url = sys.argv[1]
    if not target_url.endswith('/'): target_url += '/'
    out_folder = sys.argv[2].replace(" ", "_")

    log(f"--- Starting Download: {target_url} ---")
    mirror(target_url, target_url, out_folder, set())
    log("--- Done! ---")
