import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys

def download_recursive(url, local_path):
    if not os.path.exists(local_path):
        os.makedirs(local_path)

    try:
        response = requests.get(url, timeout=10)
        # If it's a directory listing (common for these game folders)
        if "Index of" in response.text or response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a'):
                href = link.get('href')
                if href in ['../', './', '/'] or '?' in href:
                    continue
                
                full_url = urljoin(url, href)
                # Keep it within the same game folder
                if not full_url.startswith(url):
                    continue

                local_file = os.path.join(local_path, href.strip('/'))

                if href.endswith('/'):
                    # It's a subdirectory
                    download_recursive(full_url, local_file)
                else:
                    # It's a file
                    print(f"Downloading: {href}")
                    with requests.get(full_url, stream=True) as r:
                        r.raise_for_status()
                        os.makedirs(os.path.dirname(local_file), exist_ok=True)
                        with open(local_file, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # These values come from GitHub Actions
    target_url = sys.argv[1]
    folder_name = sys.argv[2]
    download_recursive(target_url, folder_name)
