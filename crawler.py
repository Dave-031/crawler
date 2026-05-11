import os, requests, sys, re, time
from urllib.parse import urljoin

def download_and_scan(url, base_url, folder, visited):
    if url in visited or not url.startswith(base_url):
        return
    visited.add(url)

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200: return

        # Determine where to save the file locally
        relative_path = url.replace(base_url, "").lstrip("/")
        if not relative_path: relative_path = "index.html"
        local_path = os.path.join(folder, relative_path)
        
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(res.content)
        print(f"Downloaded: {relative_path}")

        # If it's a text-based file, look for more asset links inside it
        if url.endswith(('.html', '.js', '.json', '.css')):
            content = res.text
            # Look for common file extensions in quotes
            pattern = r'["\']([^"\']+\.(?:js|json|png|jpg|mp3|wav|ogg|atlas|fnt|xml))["\']'
            found_assets = re.findall(pattern, content)

            for asset in found_assets:
                full_asset_url = urljoin(url, asset)
                time.sleep(0.1) # Small delay
                download_and_scan(full_asset_url, base_url, folder, visited)

    except Exception as e:
        print(f"Failed {url}: {e}")

if __name__ == "__main__":
    target_url = sys.argv[1]
    folder_name = sys.argv[2].replace(" ", "_")
    download_and_scan(target_url, target_url, folder_name, set())
