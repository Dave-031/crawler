import os, requests, sys, re, time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

###############################################
# CONFIG
###############################################

MEDIA_EXT = (
    ".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac",
    ".mp4", ".webm", ".mov"
)

###############################################
# LOGGING
###############################################

def log(msg):
    print(msg)
    sys.stdout.flush()

###############################################
# STATIC CRAWLER
###############################################

def is_valid(path):
    if not path:
        return False

    if any(path.startswith(x) for x in ['javascript:', 'mailto:', 'data:']):
        return False

    filename = path.split('/')[-1].split('?')[0].split('#')[0]

    if filename.lower().endswith(MEDIA_EXT):
        return True

    return '.' in filename

def extract_links(text):
    patterns = [
        r'["\']([^"\'<>]+?\.(?:mp3|wav|ogg|m4a|aac|flac|mp4|webm|mov))["\']',
        r'url\(([^)]+?\.(?:mp3|wav|ogg|m4a|aac|flac|mp4|webm|mov))\)',
        r'Audio\(["\']([^"\'<>]+)["\']\)',
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return

        rel = url.replace(base_url, "").lstrip("/")
        if not rel or rel.endswith('/'):
            rel += "index.html"

        path = os.path.join(folder, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'wb') as f:
            f.write(res.content)

        log(f"[STATIC] DOWNLOADED: {rel}")

        ctype = res.headers.get('Content-Type', '')
        if any(x in ctype for x in ['text', 'json', 'javascript']):
            for item in extract_links(res.text):
                if is_valid(item):
                    clean_item = item.split('?')[0].split('#')[0]
                    full_url = urljoin(url, clean_item)
                    mirror(full_url, base_url, folder, visited, depth + 1)

    except Exception as e:
        log(f"[STATIC] ERROR on {url}: {e}")

###############################################
# HEADLESS BROWSER AUDIO CAPTURE
###############################################

def capture_dynamic_media(folder, base_url):
    html_files = []

    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root, f))

    log(f"[BROWSER] Found {len(html_files)} HTML pages to scan")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def save_response(response):
            url = response.url.lower()
            if any(url.endswith(ext) for ext in MEDIA_EXT):
                filename = url.split("/")[-1]
                out_path = os.path.join(folder, filename)
                try:
                    data = response.body()
                    with open(out_path, "wb") as f:
                        f.write(data)
                    log(f"[BROWSER] SAVED MEDIA: {filename}")
                except:
                    pass

        page.on("response", save_response)

        for html_path in html_files:
            rel = os.path.relpath(html_path, folder)
            file_url = "file://" + os.path.abspath(html_path)

            log(f"[BROWSER] Loading {rel}")
            try:
                page.goto(file_url)
                page.wait_for_timeout(3000)
            except Exception as e:
                log(f"[BROWSER] ERROR loading {rel}: {e}")

        browser.close()

###############################################
# MAIN
###############################################

if __name__ == "__main__":
    target_url = sys.argv[1]
    if not target_url.endswith('/'):
        target_url += '/'
    out_folder = sys.argv[2].replace(" ", "_")

    log(f"--- Starting Static Crawl: {target_url} ---")
    mirror(target_url, target_url, out_folder, set())

    log(f"--- Starting Dynamic Audio Capture ---")
    capture_dynamic_media(out_folder, target_url)

    log("--- Done! ---")
