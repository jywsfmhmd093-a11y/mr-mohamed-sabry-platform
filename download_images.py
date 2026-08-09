from pathlib import Path
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / 'static' / 'images'
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

IMAGES = {
    'pyramids.jpg': 'https://images.unsplash.com/photo-1503177119275-0aa32b3a9368?auto=format&fit=crop&w=1600&q=80',
    'sphinx.jpg': 'https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=1600&q=80',
}

for filename, url in IMAGES.items():
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req, timeout=60) as response:
        data = response.read()

    if not data:
        raise RuntimeError(f'No data downloaded for {filename}')

    target = IMAGES_DIR / filename
    target.write_bytes(data)
    print(f'Saved: {target} ({len(data)} bytes)')
