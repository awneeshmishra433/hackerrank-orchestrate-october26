import glob, os
from PIL import Image

images = glob.glob('dataset/evidence/images/*.png')
for img_path in images:
    im = Image.open(img_path)
    print(f"{os.path.basename(img_path)}: size={im.size}, mode={im.mode}, info={list(im.info.keys())}")
    for k, v in im.info.items():
        if isinstance(v, (str, bytes)):
            print(f"   info[{k}]: {str(v)[:200]}")

