import os, requests, sys, time
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def download_file(url, folder, name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        res = requests.get(url, headers=headers, stream=True, timeout=10)
        if res.status_code == 200:
            path = os.path.join(folder, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                for chunk in res.iter_content(8192):
                    f.write(chunk)
            print(f"Successfully downloaded: {name}")
            return True
    except:
        pass
    return False

def start_crawl(base_url, folder_name):
    # Ensure folder name has no spaces for Linux safety
    safe_folder = folder_name.replace(" ", "_")
    if not os.path.exists(safe_folder):
        os.makedirs(safe_folder)

    # 1. Try to find links automatically
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        page = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
    except:
        links = []

    # 2. Add 'Guaranteed' files to check if no links found
    test_files = ['index.html', 'main.js', 'game.js', 'style.css', 'manifest.json']
    final_list = list(set(links + test_files))

    print(f"Checking {len(final_list)} potential files...")
    for item in final_list:
        if item.startswith(('http', '?', '/')): continue
        download_file(urljoin(base_url, item), safe_folder, item)
        time.sleep(0.5) # Slow down to avoid being blocked

if __name__ == "__main__":
    if len(sys.argv) > 2:
        start_crawl(sys.argv[1], sys.argv[2])
