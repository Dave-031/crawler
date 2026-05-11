import os, requests, sys, re, time
from urllib.parse import urljoin, urlparse

def is_valid_path(path):
    """Filters out common non-file strings found in code."""
    # Ignore empty strings, external websites, or pure code snippets
    if not path or path.startswith(('http', 'data:', 'javascript:', '#')):
        return False
    # Only try to download things that have a dot (indicating a file extension)
    if '.' not in path.split('/')[-1]:
        return False
    return True

def full_mirror(url, base_url, folder, visited):
    if url in visited or not url.startswith(base_url) or len(visited) > 2000:
        return
    visited.add(url)

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200: return

        # Calculate local path
        rel_path = url.replace(base_url, "").lstrip("/")
        if not rel_path or rel_path.endswith('/'): 
            rel_path = os.path.join(rel_path, "index.html")
        
        local_path = os.path.join(folder, rel_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            f.write(res.content)
        print(f"SAVED: {rel_path}")

        # --- AGGRESSIVE DISCOVERY ---
        # If the file is text-based (HTML, JS, JSON, CSS), look inside it
        mime = res.headers.get('Content-Type', '')
        if 'text' in mime or 'json' in mime or 'javascript' in mime:
            try:
                content = res.text
                # Find EVERYTHING inside single or double quotes
                potential_links = re.findall(r'["\']([^"\']+)["\']', content)
                
                for path in set(potential_links):
                    path = path.strip()
                    if is_valid_path(path):
                        # Clean the path of queries like ?v=123
                        clean_path = path.split('?')[0].split('#')[0]
                        full_url = urljoin(url, clean_path)
                        
                        # Only follow if it's part of the same game directory
                        if full_url.startswith(base_url):
                            full_mirror(full_url, base_url, folder, visited)
            except:
                pass 

    except Exception as e:
        print(f"Error at {url}: {e}")

if __name__ == "__main__":
    start_url = sys.argv[1]
    if not start_url.endswith('/'): start_url += '/'
    
    # Use the second argument for the folder name
    target_folder = sys.argv[2].replace(" ", "_")
    
    print(f"--- STARTING FULL DOWNLOAD ---")
    print(f"Source: {start_url}")
    full_mirror(start_url, start_url, target_folder, set())
    print(f"--- DOWNLOAD COMPLETE: {target_folder} ---")
