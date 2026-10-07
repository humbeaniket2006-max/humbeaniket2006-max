"""Builds the animated profile SVGs from live GitHub contribution data.

Usage: python scripts/build_profile.py [outdir] [static]
  outdir  where to write the SVGs (default: ../assets)
  static  write the finished state with no animation (for previews)
Needs no third-party packages and no token. It reads the public contribution
calendar of PROFILE_USER (default: the repo owner) and exits without touching
any file if the page cannot be parsed.
"""
import base64, datetime as dt, math, os, re, sys, time, urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
OUT = sys.argv[1] if len(sys.argv) > 1 else str(ROOT.parent / 'assets')
STATIC = len(sys.argv) > 2 and sys.argv[2] == 'static'
USER = os.environ.get('PROFILE_USER') or os.environ.get('GITHUB_REPOSITORY_OWNER') or 'humbeaniket2006-max'

def fetch_days(user):
    url = f'https://github.com/users/{user}/contributions'
    html = ''
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'profile-readme-builder'})
            html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')
            if 'data-date' in html: break
        except Exception as e:
            print('fetch failed:', e, file=sys.stderr)
        time.sleep(3 * (attempt + 1))
    cells = re.findall(r'<td[^>]*?data-date="([\d-]+)"[^>]*?id="([^"]+)"[^>]*?data-level="(\d)"', html)
    tips = dict(re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html))
    out = []
    for date, cid, level in cells:
        m = re.match(r'(\d+) contribution', tips.get(cid, ''))
        out.append({'date': date, 'level': int(level), 'count': int(m.group(1)) if m else 0})
    out.sort(key=lambda d: d['date'])
    if len(out) < 300:
        sys.exit(f'Could not read the contribution calendar ({len(out)} days found). Leaving existing files unchanged.')
    return out

days = fetch_days(USER)
for d in days: d['d'] = dt.date.fromisoformat(d['date'])
os.makedirs(OUT, exist_ok=True)
TOTAL = sum(d['count'] for d in days)
N = len(days)
# stats
def streaks():
    best = (0, None, None); cur = (0, None, None)
    run = 0; start = None
    for i, d in enumerate(days):
        if d['count'] > 0:
            if run == 0: start = d['d']
            run += 1
            if run > best[0]: best = (run, start, d['d'])
        else: run = 0
    # current: ignore an empty final day (today not finished), as GitHub does
    i = N - 1
    if days[i]['count'] == 0: i -= 1
    end = days[i]['d']; n = 0
    while i >= 0 and days[i]['count'] > 0: n += 1; i -= 1
    cur = (n, days[i + 1]['d'] if n else None, end if n else None)
    return cur, best
CUR, BEST = streaks()
ACTIVE = sum(1 for d in days if d['count'] > 0)
BESTDAY = max(days, key=lambda d: d['count'])
AVG = TOTAL / ACTIVE if ACTIVE else 0
months = []
for d in days:
    k = (d['d'].year, d['d'].month)
    if not months or months[-1][0] != k: months.append([k, 0])
    months[-1][1] += d['count']
def fd(x): return x.strftime('%b ') + str(x.day) if x else ''
print('total', TOTAL, 'active', ACTIVE, 'cur', CUR, 'best', BEST, 'bestday', BESTDAY['date'], BESTDAY['count'], 'avg', round(AVG, 1))
print('months', [(k, v) for k, v in months])

T = {
 'dark':  dict(bg='#0d1117', panel='#0b1420', key='#2ee6d6', val='#e6edf3', mu='#7d8da1', pr='#7ee787', line='#1d6f6a', border='#2ee6d6',
               tile='#111b27', tb='#1f3040', big='#7ee787', heat=['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353'], flash='#9dffb0', bar='#26a641', barhi='#39d353', ascii='#2ee6d6'),
 'light': dict(bg='#ffffff', panel='#f6f8fa', key='#0a7f76', val='#1f2328', mu='#57606a', pr='#1a7f37', line='#d0d7de', border='#0a7f76',
               tile='#f6f8fa', tb='#d0d7de', big='#1a7f37', heat=['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'], flash='#0f5323', bar='#30a14e', barhi='#216e39', ascii='#0a6b64'),
}

def css(c):
    reduced = ('*{animation:none!important;opacity:1!important;clip-path:none!important;transform:none!important}.st{display:none!important}.cur{opacity:1!important}')
    return f'''<style>
.m{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}}
.k{{fill:{c['key']};font-size:12px;font-weight:700}}
.v{{fill:{c['val']};font-size:12px}}
.mu{{fill:{c['mu']};font-size:11px}}
.pr{{fill:{c['pr']};font-size:12px;font-weight:700}}
.p{{font-size:11px}}
.big{{font-size:26px;font-weight:700}}
.t{{clip-path:inset(0 100% 0 0)}}
.f,.st,.bar,.cell,.fin{{opacity:0}}
.cur{{animation:blink 1s steps(1) infinite}}
.l0{{--c:{c['heat'][0]};--f:{c['heat'][0]}}}.l1{{--c:{c['heat'][1]};--f:{c['flash']}}}.l2{{--c:{c['heat'][2]};--f:{c['flash']}}}.l3{{--c:{c['heat'][3]};--f:{c['flash']}}}.l4{{--c:{c['heat'][4]};--f:{c['flash']}}}
.bar{{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0)}}
@keyframes typ{{to{{clip-path:inset(0 0 0 0)}}}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes rev{{to{{clip-path:inset(0 0 0 0)}}}}
@keyframes st{{from{{opacity:1}}to{{opacity:0}}}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
@keyframes cell{{from{{opacity:0;fill:var(--f)}}to{{opacity:1;fill:var(--c)}}}}
@keyframes grow{{to{{opacity:1;transform:scaleY(1)}}}}
{('' if not STATIC else reduced)}
@media (prefers-reduced-motion:reduce){{{reduced}}}
</style>'''

def typed(inner, n, delay, per=0.045):
    dur = max(0.3, n * per)
    return f'<g class="t" style="animation:typ {dur:.2f}s steps({n}) {delay:.2f}s forwards">{inner}</g>', dur
def faded(inner, delay, dur=0.35):
    return f'<g class="f" style="animation:fade {dur}s ease-out {delay:.2f}s forwards">{inner}</g>'
def countup(vals, t0, dur, x, y, cls, final_txt, unit=None, unit_cls=None, anchor=None, attrs=''):
    """Stack of texts, each visible for one step, last one stays."""
    out = []; n = len(vals)
    dt_ = dur / n
    a = f' text-anchor="{anchor}"' if anchor else ''
    for i, v in enumerate(vals):
        u = f'<tspan class="{unit_cls}" dx="5" style="font-weight:400">{escape(unit)}</tspan>' if unit else ''
        if i < n - 1:
            out.append(f'<text class="m {cls} st" x="{x}" y="{y}"{a}{attrs} style="animation:st {dt_:.3f}s steps(1) {t0 + i * dt_:.3f}s forwards">{v}{u}</text>')
        else:
            out.append(f'<text class="m {cls} fin" x="{x}" y="{y}"{a}{attrs} style="animation:fade .05s {t0 + i * dt_:.3f}s forwards">{final_txt}{u}</text>')
    return '\n'.join(out)
def ease(final, steps=22, dec=0):
    vals = []
    for i in range(1, steps + 1):
        v = final * (1 - (1 - i / steps) ** 3)
        vals.append(round(v, dec) if dec else int(round(v)))
    vals[-1] = round(final, dec) if dec else int(final)
    out = []
    for v in vals:
        s = f'{v:.{dec}f}' if dec else f'{v:,}'
        if not out or out[-1] != s: out.append(s)
    return out

def wrap(w, h, title, desc, c, body, extra_defs=''):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t d">
<title id="t">{escape(title)}</title>
<desc id="d">{escape(desc)}</desc>
{css(c)}
<defs>{extra_defs}</defs>
{body}
</svg>
'''

PHOTO = base64.b64encode(open(ROOT / 'photo.jpg', 'rb').read()).decode()

# ---------------------------------------------------------------- card
INFO = [('Name', 'Aniket Humbe'), ('Role', 'Data Science student, builder'), ('Study', 'IIT Madras, IVB Chennai'),
        ('Focus', 'Edge AI, computer vision, LLM tooling'), ('Now', 'Hexalog: automation and AI agents')]
PROJ = [('EHMR AI', 'Senior-care health platform'), ('Ads Library MCP', 'Internal ads library tool'), ('Ocular-Core', 'Synthetic data, no GPU'),
        ('Brand Knowledge Auto-Builder', 'D2C knowledge packs'), ('Freshsales MCP', 'CRM data for Claude'), ('CRM Lead Service', 'Web leads into Freshsales')]

def card(theme):
    c = T[theme]; b = []
    b.append(f'<rect x="8" y="8" width="884" height="414" rx="16" fill="{c["bg"]}" stroke="{c["line"]}" stroke-width="1.5"/>')
    b.append('<circle cx="34" cy="36" r="6" fill="#ff5f56"/><circle cx="54" cy="36" r="6" fill="#ffbd2e"/><circle cx="74" cy="36" r="6" fill="#27c93f"/>')
    g, _ = typed(f'<text class="m k" x="96" y="40">aniket/README.md</text>', 16, 0.1, 0.03); b.append(g)
    b.append(f'<line x1="24" y1="54" x2="876" y2="54" stroke="{c["line"]}" stroke-width="1"/>')
    # photo draws in top to bottom
    b.append(f'<g class="t" style="clip-path:inset(0 0 100% 0);animation:rev 1.7s cubic-bezier(.4,0,.2,1) .3s forwards"><image x="40" y="76" width="330" height="300" preserveAspectRatio="xMidYMid slice" clip-path="url(#pclip)" xlink:href="data:image/jpeg;base64,{PHOTO}"/></g>')
    b.append(faded(f'<rect x="40" y="76" width="330" height="300" rx="8" fill="none" stroke="{c["border"]}" stroke-width="1.5"/>', 0.3, 1.7))
    b.append(faded(f'<rect x="394" y="76" width="466" height="300" rx="8" fill="{c["panel"]}" stroke="{c["border"]}" stroke-width="1.5" stroke-opacity=".8"/>', 0.5, 0.5))
    t = 1.0
    b.append(faded('<text class="m pr" x="414" y="104">aniket@dev:~$</text>', t, 0.15))
    g, d = typed('<text class="m v" x="524" y="104">./profile.sh</text>', 12, t + 0.2, 0.06); b.append(g); t += 0.2 + d + 0.25
    y = 130
    for k, v in INFO:
        n = len(k) + 2 + 6 + len(v) // 3
        inner = f'<text class="m k" x="426" y="{y}">&gt; {k}</text><text class="m v" x="500" y="{y}">{escape(v)}</text>'
        # type the value characters: steps follow bbox width
        n = max(8, int((74 + len(v) * 7.2) / 7.2))
        g, d = typed(inner, n, t, 0.022); b.append(g); t += d * 0.55 + 0.1; y += 18
    t += 0.1
    g, d = typed('<text class="m k" x="414" y="228">&gt; Projects</text>', 10, t, 0.04); b.append(g); t += d + 0.1
    y = 248
    for n_, d_ in PROJ:
        inner = (f'<text class="m mu p" x="430" y="{y}">+</text><text class="m k p" x="446" y="{y}">{escape(n_)}</text>'
                 f'<text class="m v p" x="645" y="{y}">{escape(d_)}</text>')
        n = int((645 - 430 + len(d_) * 6.6) / 6.6)
        g, d = typed(inner, n, t, 0.012); b.append(g); t += d * 0.6 + 0.08; y += 17
    t += 0.2
    b.append(faded(f'<text class="m pr" x="414" y="364">aniket@dev:~$</text><rect class="cur" x="524" y="354" width="8" height="13" fill="{c["pr"]}"/>', t, 0.2))
    desc = ('Photo of Aniket Humbe. Data Science student and builder at IIT Madras and IVB Chennai. Focus: edge AI, computer vision, LLM tooling. '
            'Working on automation and AI agents at Hexalog. Projects: ' + ', '.join(p for p, _ in PROJ) + '.')
    return wrap(900, 430, 'Profile card for Aniket Humbe', desc, c, '\n'.join(b), '<clipPath id="pclip"><rect x="40" y="76" width="330" height="300" rx="8"/></clipPath>'), t

# ---------------------------------------------------------------- contributions
def contributions(theme, t0=0.0):
    c = T[theme]; b = []; W, H = 900, 262
    b.append(f'<rect x="8" y="8" width="884" height="{H-16}" rx="16" fill="{c["bg"]}" stroke="{c["line"]}" stroke-width="1.5"/>')
    b.append(faded(f'<text class="m mu" x="36" y="36">{USER} / README.md</text>', t0 + 0.05, 0.3))
    g, d = typed(f'<text class="m pr" x="450" y="72" text-anchor="middle">aniket@github ~ $ <tspan class="v" style="font-weight:400">./contributions.sh</tspan></text>', 36, t0 + 0.2, 0.04); b.append(g)
    ts = t0 + 0.2 + d + 0.15
    X0, Y0, P, S = 70, 112, 15, 12
    first = days[0]['d']
    cols = (days[-1]['d'] - first).days // 7 + 1
    last_label_col = -9; labels = []
    for w in range(cols):
        sd = first + dt.timedelta(days=7 * w)
        if w == 0 or sd.month != (first + dt.timedelta(days=7 * (w - 1))).month:
            if w - last_label_col >= 3:
                labels.append((w, sd.strftime('%b'))); last_label_col = w
    b.append(faded(''.join(f'<text class="m mu" x="{X0 + w * P}" y="{Y0 - 8}" style="font-size:10px">{m}</text>' for w, m in labels), ts, 0.4))
    b.append(faded(''.join(f'<text class="m mu" x="36" y="{Y0 + r * P + 10}" style="font-size:10px">{n}</text>' for r, n in [(1, 'Mon'), (3, 'Wed'), (5, 'Fri')]), ts, 0.4))
    cells = []
    for d_ in days:
        w = (d_['d'] - first).days // 7; r = (d_['d'].weekday() + 1) % 7
        delay = ts + w * 0.034 + r * 0.011
        lv = d_['level']
        cells.append(f'<rect class="cell l{lv}" x="{X0 + w * P}" y="{Y0 + r * P}" width="{S}" height="{S}" rx="2.5" fill="{c["heat"][lv]}" style="animation:cell .55s ease-out {delay:.2f}s forwards"/>')
    b.append('\n'.join(cells))
    tc = ts + 0.2
    # caption: the number and its label in one text element
    b.append(faded(f'<text class="m v" x="70" y="244"><tspan style="font-weight:700">{TOTAL:,}</tspan><tspan class="mu" dx="6">contributions in the last year</tspan></text>', tc, 0.5))
    lg = ''.join(f'<rect x="{770 + i * 15}" y="233" width="{S}" height="{S}" rx="2.5" fill="{c["heat"][i]}"/>' for i in range(5))
    b.append(faded(f'<text class="m mu" x="764" y="243" text-anchor="end" style="font-size:10px">Less</text>{lg}<text class="m mu" x="850" y="243" style="font-size:10px">More</text>', ts + 1.2, 0.5))
    desc = f'Contribution heatmap for the last year. {TOTAL} contributions between {fd(days[0]["d"])} and {fd(days[-1]["d"])}.'
    return wrap(W, H, 'GitHub contributions, last year', desc, c, '\n'.join(b)), ts + 2.4

# ---------------------------------------------------------------- stats
def stats(theme, t0=0.0):
    c = T[theme]; b = []; W, H = 900, 430
    pf = ROOT / ('portrait-light.txt' if theme == 'light' else 'portrait.txt')
    ascii_rows = (pf if pf.exists() else ROOT / 'portrait.txt').read_text().split('\n')
    b.append(f'<rect x="8" y="8" width="884" height="{H-16}" rx="16" fill="{c["bg"]}" stroke="{c["line"]}" stroke-width="1.5"/>')
    g, d = typed(f'<text class="m pr" x="450" y="42" text-anchor="middle">aniket@github ~ $ <tspan class="v" style="font-weight:400">whoami</tspan></text>', 25, t0 + 0.1, 0.04); b.append(g)
    ts = t0 + 0.1 + d + 0.1
    # ascii panel
    b.append(faded(f'<rect x="36" y="62" width="340" height="330" rx="8" fill="{c["panel"]}" stroke="{c["tb"]}"/><text class="m mu" x="364" y="76" text-anchor="end" style="font-size:9px">portrait.txt</text>', ts, 0.4))
    rows = []
    for i, r in enumerate(ascii_rows):
        pts = [(k, ch) for k, ch in enumerate(r) if ch != ' ']
        if not pts: continue
        y = 88 + i * 4.5
        xs = ' '.join(f'{44 + k * 2.55:.2f}' for k, _ in pts)
        txt = escape(''.join(ch for _, ch in pts))
        rows.append(f'<text class="m f" x="{xs}" y="{y:.1f}" style="font-size:4.25px;font-weight:700;fill:{c["ascii"]};animation:fade .2s ease-out {ts + 0.3 + i * 0.03:.2f}s forwards">{txt}</text>')
    b.append('\n'.join(rows))
    # tiles
    def span(a, z): return f'{fd(a)} to {fd(z)}' if a else ''
    tiles = [
        ('$ current streak', CUR[0], 0, 'days', span(CUR[1], CUR[2]), True),
        ('$ longest streak', BEST[0], 0, 'days', span(BEST[1], BEST[2]), True),
        ('$ contributions', TOTAL, 0, 'last year', f'{fd(days[0]["d"])} to {fd(days[-1]["d"])}', False),
        ('$ active days', ACTIVE, 0, f'/ {N} days', f'{ACTIVE / N * 100:.0f}% of the window', False),
        ('$ best day', BESTDAY['count'], 0, 'contributions', fd(BESTDAY['d']), False),
        ('$ avg / active day', round(AVG, 1), 1, 'contributions', 'total / active days', False),
    ]
    TX, TW, TH, GX, GY, TY = 396, 228, 72, 12, 8, 62
    for i, (lab, val, dec, unit, sub, green) in enumerate(tiles):
        x = TX + (i % 2) * (TW + GX); y = TY + (i // 2) * (TH + GY)
        td = ts + 0.6 + i * 0.3
        b.append(faded(f'<rect x="{x}" y="{y}" width="{TW}" height="{TH}" rx="8" fill="{c["tile"]}" stroke="{c["tb"]}"/>'
                       f'<text class="m mu" x="{x + 12}" y="{y + 18}" style="font-size:10px">{lab}</text>'
                       f'<text class="m mu" x="{x + 12}" y="{y + 63}" style="font-size:10px">{escape(sub)}</text>', td, 0.4))
        fill = c['big'] if green else c['val']
        final = f'{val:.{dec}f}' if dec else f'{val:,}'
        b.append(faded(f'<text class="m big" x="{x + 12}" y="{y + 46}" fill="{fill}">{final}<tspan class="mu" dx="6" style="font-weight:400">{escape(unit)}</tspan></text>', td + 0.15, 0.5))
    # bars
    BY = TY + 3 * (TH + GY)
    b.append(faded(f'<rect x="{TX}" y="{BY}" width="468" height="{62 + 330 - BY}" rx="8" fill="{c["tile"]}" stroke="{c["tb"]}"/>'
                   f'<text class="m mu" x="{TX + 12}" y="{BY + 16}" style="font-size:10px">$ contributions / month</text>', ts + 2.2, 0.4))
    mx = max(v for _, v in months) or 1
    nb = len(months); slot = 444 / nb; bw = min(22, slot - 8); base = BY + 62 + 6
    for i, ((yy, mm), v) in enumerate(months):
        h_ = max(2, v / mx * 34); x = TX + 12 + i * slot + (slot - bw) / 2
        hi = (v == mx)
        b.append(f'<rect class="bar" x="{x:.1f}" y="{base - h_:.1f}" width="{bw:.1f}" height="{h_:.1f}" rx="2" fill="{c["barhi"] if hi else c["bar"]}" style="animation:grow .7s cubic-bezier(.2,.8,.2,1) {ts + 2.7 + i * 0.07:.2f}s forwards"/>')
        b.append(faded(f'<text class="m mu" x="{x + bw / 2:.1f}" y="{base + 10}" text-anchor="middle" style="font-size:8px">{dt.date(yy, mm, 1).strftime("%b")[0]}</text>', ts + 2.7 + i * 0.07 + 0.3, 0.3))
    desc = (f'Contribution stats. Current streak {CUR[0]} days, longest streak {BEST[0]} days, {TOTAL} contributions in the last year, '
            f'{ACTIVE} active days, best day {BESTDAY["count"]} contributions, {AVG:.1f} per active day. Monthly bar chart of contributions.')
    return wrap(W, H, 'GitHub stats', desc, c, '\n'.join(b)), ts + 4.0

# ---------------------------------------------------------------- headings
def heading(theme, cmd, comment, alt, t0=0.0):
    c = T[theme]
    n = len(cmd) + 14
    g, d = typed(f'<text class="m pr" x="8" y="22" style="font-size:13px">aniket@dev:~$ <tspan class="v" style="font-weight:700">{escape(cmd)}</tspan></text>', n, t0 + 0.1, 0.035)
    cm = faded(f'<text class="m mu" x="{8 + (n + 3) * 7.8:.0f}" y="22" style="font-size:12px"># {escape(comment)}</text>', t0 + 0.1 + d + 0.1, 0.4)
    return wrap(900, 34, alt, alt, c, g + cm)

def save(name, s):
    open(f'{OUT}/{name}.svg', 'w').write(s)

for th in ('dark', 'light'):
    s, end = card(th); save(f'terminal-{th}', s)
    s, e2 = contributions(th, 4.2); save(f'contributions-{th}', s)
    s, e3 = stats(th, 6.4); save(f'stats-{th}', s)
    for nm, cmd, cm, alt, t in (('projects', './projects.sh', 'featured projects', 'Featured projects', 9.5), ('stack', './stack.sh', 'tools I use', 'Stack', 9.5), ('links', './links.sh', 'find me here', 'Links', 9.5)):
        save(f'{nm}-{th}', heading(th, cmd, cm, alt, t))
print('card ends', round(end, 1), 'contrib ends', round(e2, 1), 'stats ends', round(e3, 1))
