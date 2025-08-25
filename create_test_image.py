# create_test_image.py
from pathlib import Path
IMAGES = Path("images")
IMAGES.mkdir(exist_ok=True)
MASTER = IMAGES / "master_image.img"
# نصنع ملف 20MB للاختبار
size_mb = 20
with MASTER.open("wb") as f:
    f.write(b'\x00' * 1024 * 1024 * size_mb)
print("Created test master image:", MASTER, "size:", size_mb, "MB")
