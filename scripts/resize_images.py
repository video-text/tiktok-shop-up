from pathlib import Path
import sys
from PIL import Image

for path in Path(sys.argv[1]).glob("*.png"):
    with Image.open(path) as image:
        image.convert("RGB").resize((800, 800), Image.Resampling.LANCZOS).save(path, "PNG", optimize=True)
