"""make_svgs.py: builds hero.svg (the brand lockup, animated) and divider.svg for SoulCraft-Org's profile README (profile/README.md).

The lockup PNG (rendered by the brand repo's build.py with the real Outfit and Lora fonts) is embedded as the base
layer, so the type is exact on GitHub, which loads no web fonts inside an SVG image. Everything animated is drawn
over it at the lockup's own coordinates (lockup-horizontal.svg: the mark is translate(40,60) scale(0.66) of a
600x600 group whose star centre is (300,296), so (238,255) here).
"""
import base64
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).parent
# usage: python3 make_svgs.py <lockup-horizontal.png> [out dir, default: beside this script]
#   the PNG is SoulCraft-Org/SoulCraft-Brand's 01_Brand/logo/lockup-horizontal.png
lockup = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "lockup-horizontal.png"
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else HERE
png = base64.b64encode(lockup.read_bytes()).decode()

CX, CY = 238, 255                     # the gold star's centre in the 1600x520 lockup
ORX, ORY, TILT = 153, 99, -22         # the violet orbit ellipse (232x150 at scale 0.66, rotated -22)

# Twinkling stars only where the artwork is empty: above and below the wordmark, and the right-hand field.
random.seed(7)
spots = [(x, y) for x, y in [
    (470, 60), (560, 118), (700, 40), (820, 96), (960, 52), (1090, 120), (1240, 70), (1330, 150), (1420, 44),
    (1540, 110), (1500, 230), (1290, 260), (1560, 340), (1400, 400), (1270, 470), (1120, 430), (980, 486),
    (820, 440), (660, 470), (520, 430), (1460, 488), (60, 40), (120, 490), (410, 470)]]
stars = []
for i, (x, y) in enumerate(spots):
    r = random.choice([1.4, 1.7, 2.0, 2.4])
    dur = random.uniform(2.6, 5.2)
    delay = random.uniform(0, 5)
    fill = "#F5F3EC" if i % 5 else "#E8C25A"
    stars.append(f'<circle class="tw" cx="{x}" cy="{y}" r="{r}" fill="{fill}" '
                 f'style="animation-duration:{dur:.1f}s;animation-delay:-{delay:.1f}s"/>')

spark = "M0,-9 Q1.4,-1.4 9,0 Q1.4,1.4 0,9 Q-1.4,1.4 -9,0 Q-1.4,-1.4 0,-9 Z"   # a four-point spark, the brand's star
orbit = f"M{CX + ORX},{CY} A{ORX},{ORY} 0 1 1 {CX - ORX},{CY} A{ORX},{ORY} 0 1 1 {CX + ORX},{CY}"

hero = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 520" width="1600" height="520" role="img" aria-label="SoulCraft: crafting AI for human flourishing">
  <title>SoulCraft</title>
  <style>
    .tw {{ animation-name: tw; animation-iteration-count: infinite; animation-timing-function: ease-in-out; }}
    @keyframes tw {{ 0%, 100% {{ opacity: .15 }} 50% {{ opacity: .95 }} }}
    .breath {{ animation: breath 6s ease-in-out infinite; transform-origin: {CX}px {CY}px; }}
    @keyframes breath {{ 0%, 100% {{ opacity: .10; transform: scale(.92) }} 50% {{ opacity: .55; transform: scale(1.06) }} }}
    .shoot {{ animation: shoot 9s ease-in infinite; }}
    @keyframes shoot {{ 0%, 78% {{ opacity: 0; transform: translate(0,0) }} 80% {{ opacity: 1 }}
                         92%, 100% {{ opacity: 0; transform: translate(-260px, 100px) }} }}
    @media (prefers-reduced-motion: reduce) {{ .tw, .breath, .shoot {{ animation: none }} .sat {{ display: none }} }}
  </style>
  <defs>
    <clipPath id="card"><rect width="1600" height="520" rx="28"/></clipPath>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#F6E2A0" stop-opacity=".9"/>
      <stop offset="40%" stop-color="#E8C25A" stop-opacity=".35"/>
      <stop offset="100%" stop-color="#E8C25A" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="tail" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#FBF1CE" stop-opacity=".95"/>
      <stop offset="100%" stop-color="#F5F3EC" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <g clip-path="url(#card)">
    <image width="1600" height="520" href="data:image/png;base64,{png}"/>
    {"".join(stars)}
    <circle class="breath" cx="{CX}" cy="{CY}" r="150" fill="url(#glow)" style="mix-blend-mode:screen"/>
    <g class="shoot"><line x1="1390" y1="34" x2="1500" y2="-10" stroke="url(#tail)" stroke-width="2.2" stroke-linecap="round"/></g>
    <g transform="rotate({TILT} {CX} {CY})">
      <g class="sat">
        <path d="{spark}" fill="#FBF1CE" opacity=".95">
          <animateMotion dur="16s" repeatCount="indefinite" path="{orbit}"/>
        </path>
      </g>
    </g>
  </g>
</svg>
'''

divider = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 48" width="1600" height="48" role="img" aria-label="">
  <style>
    .tw {{ animation: tw 3.6s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    @keyframes tw {{ 0%, 100% {{ opacity: .35; transform: scale(.8) }} 50% {{ opacity: 1; transform: scale(1.15) }} }}
    @media (prefers-reduced-motion: reduce) {{ .tw {{ animation: none }} }}
  </style>
  <defs>
    <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#E8C25A" stop-opacity="0"/>
      <stop offset="50%" stop-color="#E8C25A" stop-opacity=".85"/>
      <stop offset="100%" stop-color="#E8C25A" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="160" y="23.5" width="1280" height="1.2" fill="url(#line)"/>
  <g transform="translate(800 24) scale(2.2)"><path class="tw" d="{spark}" fill="#E8C25A"/></g>
  <g transform="translate(738 24) scale(1.15)"><path class="tw" style="animation-delay:-1.2s" d="{spark}" fill="#8B6CE0"/></g>
  <g transform="translate(862 24) scale(1.15)"><path class="tw" style="animation-delay:-2.4s" d="{spark}" fill="#8B6CE0"/></g>
</svg>
'''

(out / "hero.svg").write_text(hero)
(out / "divider.svg").write_text(divider)
print(f"hero.svg {len(hero) // 1024} KB, divider.svg {len(divider)} bytes -> {out}")
