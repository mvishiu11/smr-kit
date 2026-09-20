"""Generate README assets: animated terminal demo (GIF), hero banner (animated SVG), architecture diagram (SVG).
Run: python docs/assets/make_assets.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# ------------------------------------------------------------------ terminal demo GIF
SESSION = [
    ("cmd", "python run_all.py --mc 300"),
    ("out", "[central] S1a_smr_cfd: NPV 449 m PLN, LCOE 488, CF 0.91, premium -14 PLN/MWh (6s)"),
    ("out", "[central] S1b_smr_fixed_spotavg: NPV -896 m PLN, LCOE 480, CF 0.94, premium 27 PLN/MWh (0s)"),
    ("out", "[central] S1c_smr_merchant_baseload: NPV -5995 m PLN, LCOE 601, CF 0.94, premium 265 PLN/MWh (0s)"),
    ("out", "[central] S2_smr_dynamic: NPV -6015 m PLN, LCOE 630, CF 0.89, premium 280 PLN/MWh (6s)"),
    ("out", "[central] S3a_gas_ccgt: NPV -1737 m PLN, LCOE 962, CF 0.17, premium 372 PLN/MWh (28s)"),
    ("out", "[central] S3b_gas_ocgt: NPV -1010 m PLN, LCOE 1867, CF 0.04, premium 899 PLN/MWh (15s)"),
    ("out", "[central] S3c_gas_engines: NPV -224 m PLN, LCOE 1102, CF 0.10, premium 347 PLN/MWh (19s)"),
    ("ok", "[central] break-even strike 121.4 EUR/MWh; break-even capex 39,678 PLN/kW"),
    ("out", "MC draw 300/300  ...  P(NPV>0 | SMR CfD 125 EUR) = 27 %"),
    ("ok", "done in 689s  ->  results/summary.csv, figures/*.png"),
    ("cmd", "python build_excel.py"),
    ("ok", "saved excel/SMR_vs_Alternatives_Financial_Model.xlsx  (27,617 formulas, 0 errors)"),
    ("cmd", 'python -c "from smrtwin import *; ..."  # see README > Usage'),
]
W, H = 980, 470
BG, FG, DIM, GRN, BLU, ORG = (16, 18, 24), (222, 224, 230), (120, 124, 135), (27, 175, 122), (57, 135, 229), (235, 104, 52)


def draw_frame(lines: list[tuple[str, str]], cursor: bool) -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(MONO, 15); fb = ImageFont.truetype(MONO_B, 15)
    # window chrome
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=10, fill=BG, outline=(45, 48, 58))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([16 + i * 22, 12, 28 + i * 22, 24], fill=c)
    d.text((W // 2 - 110, 10), "smr-kit — digital twin pipeline", font=f, fill=DIM)
    y = 44
    for kind, text in lines[-18:]:
        if kind == "cmd":
            d.text((18, y), "❯", font=fb, fill=GRN); d.text((40, y), text, font=fb, fill=FG)
        elif kind == "ok":
            d.text((18, y), "✔ " + text, font=f, fill=GRN)
        else:
            col = BLU if text.startswith("[") else DIM
            d.text((18, y), text[:118], font=f, fill=col)
        y += 22
    if cursor:
        d.rectangle([40, y + 2, 49, y + 18], fill=FG)
    return im


def terminal_gif():
    frames, durs = [], []
    shown: list[tuple[str, str]] = []
    for kind, text in SESSION:
        if kind == "cmd":
            for i in range(1, len(text) + 1, 2):        # typing
                frames.append(draw_frame(shown + [("cmd", text[:i])], True)); durs.append(35)
            frames.append(draw_frame(shown + [("cmd", text)], True)); durs.append(500)
            shown.append((kind, text))
        else:
            shown.append((kind, text))
            frames.append(draw_frame(shown, False)); durs.append(320 if kind == "out" else 700)
    frames.append(draw_frame(shown, True)); durs.append(2500)
    frames[0].save(HERE / "demo.gif", save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=True)


# ------------------------------------------------------------------ hero banner (animated SVG)
BANNER = """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="260" viewBox="0 0 1200 260">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#0d366b"><animate attributeName="stop-color" values="#0d366b;#1c5cab;#0d366b" dur="8s" repeatCount="indefinite"/></stop>
      <stop offset="100%" stop-color="#1baf7a"><animate attributeName="stop-color" values="#1baf7a;#2a78d6;#1baf7a" dur="8s" repeatCount="indefinite"/></stop>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.18"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="260" rx="18" fill="url(#g)"/>
  <rect width="300" height="260" fill="url(#shine)"><animate attributeName="x" from="-300" to="1200" dur="5s" repeatCount="indefinite"/></rect>
  <!-- price curve -->
  <polyline fill="none" stroke="#ffffff" stroke-opacity="0.35" stroke-width="3" stroke-linejoin="round"
    points="720,180 760,120 800,150 840,90 880,140 920,60 960,130 1000,100 1040,160 1080,70 1120,120 1160,95">
    <animate attributeName="stroke-dasharray" values="0,1200;1200,0" dur="4s" repeatCount="indefinite"/>
  </polyline>
  <g fill="#ffffff" fill-opacity="0.9">
    <rect x="730" y="200" width="18" height="30" rx="3"><animate attributeName="height" values="30;12;30" dur="3s" repeatCount="indefinite"/><animate attributeName="y" values="200;218;200" dur="3s" repeatCount="indefinite"/></rect>
    <rect x="756" y="190" width="18" height="40" rx="3"/>
    <rect x="782" y="200" width="18" height="30" rx="3"><animate attributeName="height" values="30;40;30" dur="2.2s" repeatCount="indefinite"/><animate attributeName="y" values="200;190;200" dur="2.2s" repeatCount="indefinite"/></rect>
    <rect x="808" y="205" width="18" height="25" rx="3"/>
  </g>
  <circle cx="1090" cy="200" r="26" fill="none" stroke="#fff" stroke-opacity="0.8" stroke-width="3"/>
  <circle cx="1090" cy="200" r="8" fill="#fff"><animate attributeName="r" values="8;12;8" dur="2s" repeatCount="indefinite"/></circle>
  <g stroke="#fff" stroke-opacity="0.8" stroke-width="3" stroke-linecap="round">
    <line x1="1090" y1="160" x2="1090" y2="170"/><line x1="1090" y1="230" x2="1090" y2="240"/>
    <line x1="1050" y1="200" x2="1060" y2="200"/><line x1="1120" y1="200" x2="1130" y2="200"/>
    <animateTransform attributeName="transform" type="rotate" from="0 1090 200" to="360 1090 200" dur="12s" repeatCount="indefinite"/>
  </g>
  <text x="56" y="105" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif" font-size="54" font-weight="700" fill="#fff">smr-kit</text>
  <text x="56" y="150" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif" font-size="22" fill="#fff" fill-opacity="0.95">Digital twin: BWRX-300 SMR vs gas on the Polish power market</text>
  <text x="56" y="190" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif" font-size="16" fill="#fff" fill-opacity="0.8">hourly dispatch · CfD / merchant / dynamic · finance &amp; tax · optimisation · Monte Carlo · Excel</text>
</svg>
"""

# ------------------------------------------------------------------ architecture diagram (SVG)
ARCH = """<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="560" viewBox="0 0 1100 560" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif">
  <defs>
    <marker id="a" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#52514e"/></marker>
    <style>
      .box{fill:#fcfcfb;stroke:#2a78d6;stroke-width:2;rx:12}
      .box2{fill:#fcfcfb;stroke:#eb6834;stroke-width:2}
      .box3{fill:#fcfcfb;stroke:#1baf7a;stroke-width:2}
      .box4{fill:#fcfcfb;stroke:#4a3aa7;stroke-width:2}
      .t{font-size:15px;font-weight:700;fill:#0b0b0b}
      .s{font-size:12px;fill:#52514e}
      .e{stroke:#52514e;stroke-width:2;fill:none;marker-end:url(#a)}
      .flow{stroke:#2a78d6;stroke-width:3;fill:none;stroke-dasharray:8 8;animation:dash 1.2s linear infinite}
      @keyframes dash{to{stroke-dashoffset:-32}}
    </style>
  </defs>
  <rect width="1100" height="560" fill="#ffffff"/>
  <!-- data -->
  <rect x="30" y="40" width="230" height="110" rx="12" class="box"/>
  <text x="45" y="65" class="t">data/raw</text>
  <text x="45" y="88" class="s">PSE csdac-pln (15-min SDAC prices)</text>
  <text x="45" y="106" class="s">energy-charts DA prices, NBP FX</text>
  <text x="45" y="124" class="s">TGE monthly reports (forwards)</text>
  <!-- prices -->
  <rect x="320" y="40" width="250" height="110" rx="12" class="box"/>
  <text x="335" y="65" class="t">prices.py — market twin</text>
  <text x="335" y="88" class="s">8,760-h reference year → shape model</text>
  <text x="335" y="106" class="s">re-anchor on annual mean path</text>
  <text x="335" y="124" class="s">+ solar cannibalisation per year</text>
  <!-- assumptions -->
  <rect x="640" y="40" width="230" height="110" rx="12" class="box4"/>
  <text x="655" y="65" class="t">assumptions/default.yaml</text>
  <text x="655" y="88" class="s">every parameter [low, central, high]</text>
  <text x="655" y="106" class="s">≈200 sources, config.resolve(case)</text>
  <text x="655" y="124" class="s">per-block overrides (smr/market/…)</text>
  <!-- smr -->
  <rect x="120" y="220" width="300" height="120" rx="12" class="box"/>
  <text x="135" y="245" class="t">smr.py — BWRX-300 twin</text>
  <text x="135" y="268" class="s">870 MWt / 300 MWe · 18-mo refuelling · EFOR</text>
  <text x="135" y="286" class="s">50–100 % load-following, 0.5 %/min ramp</text>
  <text x="135" y="304" class="s">LP dispatch (HiGHS) · CfD settlement</text>
  <text x="135" y="322" class="s">marginal cost = fuel + VOM + fund</text>
  <!-- gas -->
  <rect x="460" y="220" width="300" height="120" rx="12" class="box2"/>
  <text x="475" y="245" class="t">gas.py — CCGT / OCGT / engines</text>
  <text x="475" y="268" class="s">2-segment heat rate · min load · min up/down</text>
  <text x="475" y="286" class="s">hot/warm/cold starts · EUA cost</text>
  <text x="475" y="304" class="s">weekly UC-MILP (HiGHS)</text>
  <text x="475" y="322" class="s">+ DP heuristic (≤1 % gap) for Monte Carlo</text>
  <!-- finance -->
  <rect x="120" y="400" width="300" height="120" rx="12" class="box3"/>
  <text x="135" y="425" class="t">finance.py — cash flows &amp; tax</text>
  <text x="135" y="448" class="s">S-curve capex · KŚT depreciation · CIT 19 %</text>
  <text x="135" y="466" class="s">NPV / IRR / LCOE / levelised revenue</text>
  <text x="135" y="484" class="s">property tax (art. 50 split), JST CIT/PIT shares</text>
  <text x="135" y="502" class="s">optional debt overlay (DSCR, equity IRR)</text>
  <!-- optimise -->
  <rect x="460" y="400" width="300" height="120" rx="12" class="box3"/>
  <text x="475" y="425" class="t">optimise.py</text>
  <text x="475" y="448" class="s">break-even strike / capex / premium (Brent)</text>
  <text x="475" y="466" class="s">integer portfolio optimum (≥300 MW firm)</text>
  <text x="475" y="484" class="s">LHS Monte Carlo · tornado</text>
  <!-- outputs -->
  <rect x="820" y="220" width="250" height="300" rx="12" class="box4"/>
  <text x="835" y="245" class="t">outputs</text>
  <text x="835" y="272" class="s">results/summary.csv</text>
  <text x="835" y="290" class="s">results/&lt;case&gt;/&lt;scenario&gt;/*</text>
  <text x="835" y="308" class="s">figures/*.png</text>
  <text x="835" y="326" class="s">docs/RESULTS.md</text>
  <text x="835" y="360" class="t">build_excel.py →</text>
  <text x="835" y="382" class="s">Excel model, 27k live formulas</text>
  <text x="835" y="400" class="s">Dashboard · Input · Model_* · Twin</text>
  <text x="835" y="440" class="t">scenarios.py / run_all.py</text>
  <text x="835" y="462" class="s">S1a CfD · S1b fixed · S1c merchant</text>
  <text x="835" y="480" class="s">S2 dynamic · S3a–d gas</text>
  <!-- edges -->
  <path d="M260,95 L320,95" class="e"/>
  <path d="M445,150 L300,220" class="flow"/>
  <path d="M445,150 L600,220" class="flow"/>
  <path d="M755,150 L640,220" class="e"/>
  <path d="M755,150 L270,220" class="e"/>
  <path d="M270,340 L270,400" class="flow"/>
  <path d="M610,340 L330,400" class="flow"/>
  <path d="M420,460 L460,460" class="e"/>
  <path d="M760,460 L820,460" class="flow"/>
  <path d="M760,280 L820,280" class="e"/>
</svg>
"""


if __name__ == "__main__":
    terminal_gif()
    (HERE / "banner.svg").write_text(BANNER, encoding="utf-8")
    (HERE / "architecture.svg").write_text(ARCH, encoding="utf-8")
    print("assets written to", HERE)
