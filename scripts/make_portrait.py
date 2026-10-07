"""Turns photo.jpg into the ASCII portraits used by build_profile.py.

Usage: python scripts/make_portrait.py
Needs Pillow, numpy, scipy and scikit-learn (only for this one-off step, the
workflow does not run it). Writes portrait.txt (light characters on a dark
panel) and portrait-light.txt (dark characters on a light panel).
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from sklearn.mixture import GaussianMixture

ROOT = Path(__file__).resolve().parent
COLS, ROWS = 128, 66
CROP = (62, 30, 372, 312)   # box around the face in photo.jpg, same shape as the character grid
RAMP = " .:-=+*#%@"

# rough head and shoulders outline in photo.jpg pixels (440x400), refined by colour below
OUTLINE = [(103, 135), (114, 82), (160, 48), (215, 40), (250, 52), (272, 72), (286, 100), (300, 128), (311, 160),
           (321, 192), (316, 222), (302, 256), (322, 272), (440, 318), (440, 400), (0, 400), (8, 388), (95, 322),
           (180, 300), (150, 268), (124, 254), (110, 236), (108, 200)]

def subject_mask(img):
    """Soft 0..1 mask of the person. The outline is only a prior: pixels near its edge
    are decided by whether their colour looks like the inside or the outside."""
    w, h = img.size
    poly = Image.new('L', (w, h), 0)
    ImageDraw.Draw(poly).polygon(OUTLINE, fill=255)
    inside = np.array(poly) > 0
    d_in, d_out = ndi.distance_transform_edt(inside), ndi.distance_transform_edt(~inside)
    band = 12
    rgb = np.array(img).astype(float)
    feat = np.stack([ndi.gaussian_filter(rgb[..., i], 1.0) for i in range(3)], -1).reshape(-1, 3)
    rng = np.random.default_rng(0)
    def pick(m, n=6000):
        idx = np.flatnonzero(m.ravel())
        return feat[rng.choice(idx, min(n, len(idx)), replace=False)]
    fg = GaussianMixture(6, covariance_type='full', random_state=0).fit(pick(d_in > band))
    bg = GaussianMixture(6, covariance_type='full', random_state=0).fit(pick(d_out > band))
    llr = (fg.score_samples(feat) - bg.score_samples(feat)).reshape(h, w)
    m = (llr + np.where(inside, d_in, -d_out) * 0.7) > 0
    m = ndi.binary_closing(ndi.binary_opening(m, iterations=2), iterations=4)
    lab, n = ndi.label(m)
    if n > 1:
        m = lab == 1 + int(np.argmax(ndi.sum(m, lab, range(1, n + 1))))
    m = ndi.binary_opening(ndi.binary_fill_holes(m), iterations=4)
    return Image.fromarray((ndi.gaussian_filter(m.astype(float), 1.6) * 255).astype('uint8'))

def tone(img, mask):
    """Percentile stretch inside the subject, then local contrast so eyes, brows and mouth stay crisp."""
    g = np.array(img.convert('L')).astype(float)
    sel = np.array(mask) > 128
    lo, hi = np.percentile(g[sel], (2, 98))
    g = np.clip((g - lo) / (hi - lo), 0, 1)
    g = np.clip(g + 1.4 * (g - ndi.gaussian_filter(g, 9)), 0, 1)
    g = 0.12 + 0.88 * g ** 0.9
    return Image.fromarray((g * 255).astype('uint8'))

def build(invert):
    photo = Image.open(ROOT / 'photo.jpg').convert('RGB')
    mask = subject_mask(photo).crop(CROP)
    img = photo.crop(CROP)
    g = np.array(tone(img, mask).resize((COLS, ROWS), Image.LANCZOS)).astype(float)
    m = np.array(mask.resize((COLS, ROWS), Image.LANCZOS)).astype(float) / 255
    ink = (255 - g if invert else g) * m          # soft mask: edge cells fade out instead of cutting off
    idx = np.clip((ink / 255 * (len(RAMP) - 1)).round().astype(int), 0, len(RAMP) - 1)
    return '\n'.join(''.join(RAMP[i] for i in row).rstrip() for row in idx) + '\n'

if __name__ == '__main__':
    (ROOT / 'portrait.txt').write_text(build(invert=False))
    (ROOT / 'portrait-light.txt').write_text(build(invert=True))
    print('wrote portrait.txt and portrait-light.txt')
