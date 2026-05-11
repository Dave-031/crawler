import os, requests, sys, re, time
from urllib.parse import urljoin

# This makes sure logs show up on GitHub immediately
def log(msg):
    print(msg)
    sys.stdout.flush()

# Media extensions we always want to download
MEDIA_EXT = (".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac",
             ".mp4", ".webm", ".ogg", ".mov")

def is_valid(path):
    if not path:
        return False

    # Reject only dangerous schemes
    if any(path.startswith(x) for x in ['javascript:', 'mailto:', 'data:']):
        return False

    # Strip query/hash
    filename = path.split('/')[-1].split('?')[0].split('#')[0]

    # Always accept media files
    if filename.lower().endswith(MEDIA_EXT):
        return True

    # Must have a dot for normal files
    return '.' in filename

def extract_links(text):
    patterns = [
        # Quoted media files
        r'["\']([^"\'<>]+?\.(?:mp3|wav|ogg|m4a|aac|flac|mp4|webm|mov))["\']',

        # url(file.mp3)
        r'url\(([^)]+?\.(?:mp3|wav|ogg|m4a|aac|flac|mp4|webm|mov))\)',

        # Audio("file.mp3")
        r'Audio\(["\']([^"\'<>]+)["\']\)',

        # Generic quoted strings (fallback)
        r'["\']([^"\'\s<>]+)["\']',
    ]

    found = []
    for p in patterns:
        found += re.findall(p, text, flags=re.IGNORECASE)

    return set(found)

def mirror(url, base_url, folder, visited, depth=0):
    if depth > 10 or url in visited or not url.startswith(base_url):
        return

    visited.add(url)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return

        # Determine path
        rel = url.replace(base_url, "").lstrip("/")
        if not rel or rel.endswith('/'):
            rel += "index.html"

        path = os.path.join(folder, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'wb') as f:
            f.write(res.content)

        log(f"DOWNLOADED: {rel}")

        # Scan text-like files for more links
        ctype = res.headers.get('Content-Type', '')
        if any(x in ctype for x in ['text', 'json', 'javascript']):
            for item in extract_links(res.text):
                if is_valid(item):
                    clean_item = item.split('?')[0].split('#')[0]
                    full_url = urljoin(url, clean_item)
                    mirror(full_url, base_url, folder, visited, depth + 1)

    except Exception as e:
        log(f"ERROR on {url}: {e}")

if __name__ == "__main__":
    target_url = sys.argv[1]
    if not target_url.endswith('/'):
        target_url += '/'
    out_folder = sys.argv[2].replace(" ", "_")

    log(f"--- Starting Download: {target_url} ---")
    mirror(target_url, target_url, out_folder, set())
    log("--- Done! ---")
