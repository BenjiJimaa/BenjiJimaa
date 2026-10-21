# netwatch: the contribution year as an intercept monitor (real data in, SVG out)
import datetime, random
from html import escape
def build(days, today=None):
    """days: list of (iso_date, count, level 0-4), oldest first, ~1 year"""
    rnd = random.Random(7)
    today = today or datetime.date.fromisoformat(days[-1][0])
    W, C = 1075, 9.0
    CS = 15.5
    GX, GY = 74, 98
    start = datetime.date.fromisoformat(days[0][0])
    start -= datetime.timedelta(days=start.isoweekday() % 7)          # back to sunday
    cells = {}
    for d, n, lv in days:
        dd = datetime.date.fromisoformat(d)
        c = (dd - start).days // 7; r = dd.isoweekday() % 7
        cells[(c, r)] = (d, n, lv)
    NCOL = max(c for c, _ in cells) + 1
    GW = NCOL*CS
    kt = lambda *ts: ';'.join(f'{min(1, max(0, t/C)):.4f}' for t in ts)
    def anim(attr, vals, times, discrete=True):
        return (f'<animate attributeName="{attr}"{" calcMode=\"discrete\"" if discrete else ""} values="{";".join(map(str, vals))}" '
                f'keyTimes="{kt(*times)}" dur="{C}s" repeatCount="indefinite"/>')
    T0, T1 = .5, C - 1.2                      # beam sweep window
    beam_t = lambda c: T0 + (T1 - T0) * (c + .5) / NCOL
    GL = ['·', '░', '▒', '▓', '█']
    GC = ['#2a2433', '#2b6f80', '#3ee6ff', '#9ff4ff', '#ffffff']
    out = []
    # header
    out.append(f'<text x="24" y="38" font-size="13" fill="#7a7090"><tspan fill="#ff2fae">root@void</tspan>:~# <tspan fill="#ece8ee">netwatch --target benji --window 365d</tspan></text>')
    out.append(f'<circle cx="{W-86}" cy="34" r="4" fill="#ff2fae"><animate attributeName="opacity" values="1;.2;1" dur="1.2s" repeatCount="indefinite"/></circle>'
               f'<text x="{W-24}" y="38" font-size="11" text-anchor="end" fill="#ff2fae" font-weight="700">LIVE</text>')
    out.append(f'<line x1="24" y1="52" x2="{W-24}" y2="52" stroke="#1c1822"/>')
    # month labels + weekday labels
    seen = set()
    for c in range(NCOL):
        d = start + datetime.timedelta(weeks=c)
        if d.month not in seen and d.day <= 7:
            seen.add(d.month)
            out.append(f'<text x="{GX + c*CS:.0f}" y="{GY - 12}" font-size="10" fill="#4a4260">{d.strftime("%b").lower()}</text>')
    for r, lab in ((1, 'mon'), (3, 'wed'), (5, 'fri')):
        out.append(f'<text x="{GX - 12}" y="{GY + r*CS + 10:.0f}" font-size="10" text-anchor="end" fill="#4a4260">{lab}</text>')
    # grid as glyphs
    active = []
    for (c, r), (d, n, lv) in sorted(cells.items()):
        x = GX + c*CS + CS/2; y = GY + r*CS + 11
        if lv == 0:
            out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="13" text-anchor="middle" fill="{GC[0]}">·</text>')
            continue
        active.append((c, r, d, n, lv))
        tb = beam_t(c)
        out.append(f'<text x="{x:.1f}" y="{y+1:.1f}" font-size="18" text-anchor="middle" fill="{GC[lv]}">{GL[lv]}'
                   f'{anim("fill", [GC[lv], "#ff2fae", "#ffffff", GC[lv]], [0, tb, tb + .08, tb + .3])}</text>')
        cy = GY + r*CS + CS/2
        out.append(f'<circle cx="{x:.1f}" cy="{cy:.1f}" r="3" fill="none" stroke="#ff2fae" stroke-width="1.5" opacity="0">'
                   f'{anim("r", [3, 3, 34, 34], [0, tb, tb + .6, C], False)}{anim("opacity", [0, 0, .9, 0, 0], [0, tb, tb + .02, tb + .6, C], False)}</circle>')
    # scan beam
    out.append(f'<rect y="{GY - 4}" width="{CS*1.6:.0f}" height="{7*CS + 8:.0f}" fill="#3ee6ff" opacity=".08">'
               f'{anim("x", [GX - CS*2, GX - CS*2, GX + GW, GX + GW], [0, T0, T1, C], False)}</rect>')
    out.append(f'<rect y="{GY - 4}" width="2" height="{7*CS + 8:.0f}" fill="#3ee6ff" opacity=".7">'
               f'{anim("x", [GX - CS*.4, GX - CS*.4, GX + GW + CS*1.2, GX + GW + CS*1.2], [0, T0, T1, C], False)}</rect>')
    # heartbeat line from weekly totals, traced in step with the beam
    wk = [0]*NCOL
    for (c, r), (d, n, lv) in cells.items(): wk[c] += max(n, lv)
    peak = max(1, max(wk))
    EY0, EH = GY + 7*CS + 40, 34
    pts = []
    for c in range(NCOL):
        xm = GX + c*CS + CS/2
        if wk[c] == 0:
            pts += [(xm - CS/2, EY0), (xm + CS/2, EY0)]
        else:
            h = 8 + (EH - 8) * wk[c] / peak
            pts += [(xm - CS/2, EY0), (xm - 3, EY0), (xm - 1, EY0 - h), (xm + 2, EY0 + h*.45), (xm + 4, EY0), (xm + CS/2, EY0)]
    plen = sum(((pts[i+1][0]-pts[i][0])**2 + (pts[i+1][1]-pts[i][1])**2) ** .5 for i in range(len(pts)-1))
    out.append(f'<line x1="{GX}" y1="{EY0}" x2="{GX+GW}" y2="{EY0}" stroke="#1c1822"/>')
    out.append(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="#3ee6ff" stroke-width="1.6" stroke-dasharray="{plen:.0f}" stroke-dashoffset="{plen:.0f}">'
               f'{anim("stroke-dashoffset", [round(plen), round(plen), 0, 0, round(plen)], [0, T0, T1, C - .3, C], False)}</polyline>')
    out.append(f'<text x="{GX - 12}" y="{EY0 + 4}" font-size="10" text-anchor="end" fill="#4a4260">pulse</text>')
    # intercept log (right)
    LX = GX + GW + 26
    out.append(f'<text x="{LX}" y="{GY - 12}" font-size="10" fill="#4a4260">intercept log</text>')
    out.append(f'<line x1="{LX - 14}" y1="{GY - 22}" x2="{LX - 14}" y2="{EY0 + EH}" stroke="#1c1822"/>')
    shown = sorted(active, key=lambda a: a[0])[-8:]
    for k, (c, r, d, n, lv) in enumerate(shown):
        tb = beam_t(c)
        txt = f'{d[5:]}  ' + (f'{n} commit{"s" if n != 1 else ""}' if n else f'lvl {lv}')
        out.append(f'<text x="{LX}" y="{GY + 8 + k*17}" font-size="11" fill="#b9b2c2" opacity="0"><tspan fill="#ff2fae">&gt; </tspan>{escape(txt)}'
                   f'{anim("opacity", [0, 1, 0], [0, tb, C - .3])}</text>')
    if not active:
        out.append(f'<text x="{LX}" y="{GY + 8}" font-size="11" fill="#4a4260">no signal.</text>')
    # stats
    tot = sum(max(n, 1 if lv else 0) for _, n, lv in [v for v in cells.values()])
    act_days = len(active)
    last = max((d for _, _, d, _, _ in active), default=None)
    ago = (today - datetime.date.fromisoformat(last)).days if last else None
    wd = [0]*7
    for c, r, d, n, lv in active: wd[r] += max(n, lv)
    best_wd = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'][wd.index(max(wd))] if active else '--'
    strongest = max(active, key=lambda a: (a[3] or a[4]))[2] if active else '--'
    SY = EY0 + EH + 34
    stats = [('signals', f'{act_days} days'), ('strongest', strongest), ('peak day', best_wd),
             ('last ping', 'today' if ago == 0 else (f'{ago}d ago' if ago is not None else '--'))]
    sx = 24
    for k, (a, b) in enumerate(stats):
        out.append(f'<text x="{sx}" y="{SY}" font-size="11" fill="#4a4260">{a}  <tspan fill="#ece8ee">{escape(b)}</tspan></text>')
        sx += 24 + (len(a) + len(b) + 2) * 6.6 + 18
    out.append(f'<text x="{W-24}" y="{SY}" font-size="11" text-anchor="end" fill="#4a4260">public channels only. <tspan fill="#ff2fae">the rest runs dark.</tspan></text>')
    H = int(SY + 26)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}px" height="{H}px" viewBox="0 0 {W} {H}" font-family="ConsolasFallback,Consolas,'DejaVu Sans Mono',monospace">
<style>@font-face {{ src: local('Consolas'); font-family: 'ConsolasFallback'; -webkit-size-adjust: 109%; size-adjust: 109%; }} text, tspan {{ white-space: pre; }}</style>
<defs><pattern id="asl" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity=".03"/></pattern></defs>
<rect width="{W}" height="{H}" rx="15" fill="#050406"/>
{''.join(out)}
<rect width="{W}" height="{H}" rx="15" fill="url(#asl)"/>
</svg>'''

if __name__ == '__main__':
    import json
    raw = json.load(open('activity_sample.json'))
    days = [(d, 0, lv) for d, lv in raw]
    open('activity.svg', 'w').write(build(days))
    import os; print(os.path.getsize('activity.svg')//1024, 'KB')
