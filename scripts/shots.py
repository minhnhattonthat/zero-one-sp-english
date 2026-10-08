"""Montage of screenshots: python -m scripts.shots <dir> [out.png] [scale]"""
import sys
from pathlib import Path

from PIL import Image


def montage(d, out=None, cols=6, scale=1):
    fs = sorted(Path(d).glob('f*.png'))
    W, H = 240 * scale, 160 * scale
    m = Image.new('RGB', (W * cols, H * ((len(fs) + cols - 1) // cols)))
    for i, f in enumerate(fs):
        m.paste(Image.open(f).convert('RGB').resize((W, H), Image.NEAREST), ((i % cols) * W, (i // cols) * H))
    out = out or Path(d) / 'montage.png'
    m.save(out)
    return out


if __name__ == '__main__':
    print(montage(sys.argv[1], *(sys.argv[2:3] or [None])))
