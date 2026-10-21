"""neofetch-style card: <B> logo (hacker decode) + [ benji@void ] info, real GitHub stats."""
import json, datetime, os, random
from html import escape
LOGO=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.json')))
THEMES={
 'dark': dict(bg='#050406', text='#ece8ee', key='#3ee6ff', value='#f2eef4', dots='#3a3140', add='#7dff9a', dele='#ff2fae', art='#ece6ea', mag='#ff2fae', cyan='#3ee6ff'),
}
THEMES['light']=THEMES['dark']
WIDTH=58  # characters on the right column
def kv(key, value, width=WIDTH):
    """'. Key: ....... value' padded so values end at the same column."""
    left=f'. {key}:'
    dots=width-len(left)-len(value)-2
    return left, '.'*max(1,dots), value
def section(title, width=WIDTH):
    return f'// {title.upper()} ' + '/'*(width-len(title)-4)

def age(since, today):
    y=today.year-since.year; m=today.month-since.month; d=today.day-since.day
    if d<0: m-=1; d+=(today.replace(day=1)-datetime.timedelta(days=1)).day
    if m<0: y-=1; m+=12
    return f"{y} years, {m} months, {d} days"


def stat_rows(s):
    def pair(k1,v1,k2,v2,extra=''):
        a=f'. {k1}:'; av=f'{v1}{extra}'
        left_w=30
        d1=left_w-len(a)-len(av)-2
        b=f'{k2}:'; bv=str(v2)
        d2=WIDTH-left_w-3-len(b)-len(bv)-2
        return ('raw', f'<tspan class="cc">. </tspan><tspan class="key">{k1}</tspan>:<tspan class="cc"> {"."*d1} </tspan><tspan class="value">{escape(av)}</tspan> | <tspan class="key">{k2}</tspan>:<tspan class="cc"> {"."*d2} </tspan><tspan class="value">{bv}</tspan>')
    loc=f"{s['loc']:,}"; add=f"{s['add']:,}++"; de=f"{s['del']:,}--"
    l=f'. Lines of Code on GitHub:'; tail=f'{loc} ( {add}, {de} )'
    d=WIDTH-len(l)-len(tail)-2
    return [pair('Repos',s['repos'],'Stars',s['stars'],f" {{Contributed: {s['contrib']}}}"),
            pair('Commits',s['commits'],'Followers',s['followers']),
            ('raw', f'<tspan class="cc">. </tspan><tspan class="key">Lines of Code on GitHub</tspan>:<tspan class="cc"> {"."*d} </tspan><tspan class="value">{loc}</tspan> ( <tspan class="addColor">{add}</tspan>, <tspan class="delColor">{de}</tspan> )')]


SCR = "!@#$%&*+=-~<>/\\?^"
def scramble(s, rnd, keep=0.0):
    return ''.join(ch if ch == ' ' or rnd.random() < keep else rnd.choice(SCR) for ch in s)
def scramble_digits(s, rnd):
    return ''.join(rnd.choice('0123456789') if ch.isdigit() else ch for ch in s)


def background(h, logo_top, T):
    """Original dark collage: halftone, rings, terminal scraps, old error windows, glitch bars."""
    r = random.Random(99); W = 1075
    g = []
    g.append('''<defs>
<pattern id="dots" width="4" height="4" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".75" fill="#fff"/></pattern>
<pattern id="chk" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="#fff"/><rect x="3" y="3" width="3" height="3" fill="#fff"/></pattern>
<pattern id="lines" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-35)"><rect width="6" height="1.4" fill="#fff"/></pattern>
<clipPath id="card"><rect width="1075" height="%d" rx="15"/></clipPath>
</defs>''' % h)
    g.append('<g clip-path="url(#card)">')
    # halftone wash + a diagonal hatched band across the card
    g.append(f'<rect width="{W}" height="{h}" fill="url(#dots)" opacity=".035"/>')
    g.append(f'<polygon points="380,-20 520,-20 160,{h+20} 20,{h+20}" fill="url(#lines)" opacity=".045"/>')
    g.append(f'<polygon points="700,-20 760,-20 520,{h+20} 460,{h+20}" fill="url(#chk)" opacity=".025"/>')
    # concentric broken rings behind the logo
    cx, cy = 250, logo_top + 180
    for k, rr in enumerate(range(70, 520, 16)):
        dash = f'{r.randint(20,120)} {r.randint(6,40)}'
        g.append(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="#fff" stroke-width="{1.2 if k%3 else 2.2}" stroke-dasharray="{dash}" opacity="{max(.012, .05 - k*.0015):.3f}"/>')
    # terminal scraps (very faint)
    scraps = ["C:\\SYSTEM\\kernel\\events > 0x4F2A", "(PID 54700) access denied", "root@void:~# ./override --all",
              "segfault at 0x00007ffd3c1e", "packets: 1337 sent / 0 lost", "trace ............ 13 hops",
              "decrypting payload  [#####----]", "/var/log/void.log  rotated", "whoami && id && uname -a",
              "SIGKILL received, respawning", "chmod +x ./b.sh", "0xDEADBEEF  0xCAFEBABE  0x8BADF00D"]
    spots = [(470, 26), (40, 22), (60, h-26), (300, h-12), (820, h-18), (930, 40), (540, h-40), (20, 70)]
    for (x, y), t in zip(spots, r.sample(scraps, len(spots))):
        g.append(f'<text x="{x}" y="{y}" font-size="12" fill="#fff" opacity=".07">{escape(t)}</text>')
    for k in range(6):
        y = r.randint(40, h-40); x = r.choice([-20, W-260])
        g.append(f'<text x="{x}" y="{y}" font-size="11" fill="#fff" opacity=".04">{escape(r.choice(scraps))}</text>')
    # old-OS error windows, half hidden at the edges
    for (x, y, w, t) in [(-30, h-120, 190, "fatal_error.exe"), (W-64, 150, 200, "not responding"), (W-80, h-210, 230, "epic_fail.log"), (330, -40, 150, "pwned.exe")]:
        g.append(f'<g opacity=".09"><rect x="{x}" y="{y}" width="{w}" height="78" fill="#000" stroke="#fff"/>'
                 f'<rect x="{x}" y="{y}" width="{w}" height="16" fill="#fff"/>'
                 f'<text x="{x+6}" y="{y+12}" font-size="11" fill="#000">{escape(t)}</text>'
                 f'<rect x="{x+w-14}" y="{y+3}" width="10" height="10" fill="#000"/>'
                 f'<rect x="{x+w/2-28}" y="{y+52}" width="56" height="16" fill="none" stroke="#fff"/>'
                 f'<text x="{x+w/2}" y="{y+64}" font-size="10" fill="#fff" text-anchor="middle">OK</text>'
                 f'<text x="{x+12}" y="{y+38}" font-size="11" fill="#fff">!  {escape(r.choice(["error 0x1F", "pwned.", "try again?"]))}</text></g>')
    # glitch bars with flicker
    for k in range(14):
        x = r.randint(0, W-120); y = r.randint(10, h-14); w = r.randint(30, 160); hh = r.choice([3, 5, 8, 12])
        fill = r.choice(['url(#chk)', '#fff', T['mag'], T['cyan']])
        op = .05 if fill.startswith('url') or fill == '#fff' else .07
        g.append(f'<rect x="{x}" y="{y}" width="{w}" height="{hh}" fill="{fill}" opacity="{op}" class="gb" style="animation-delay:{r.uniform(0,8):.2f}s"/>')
    g.append('</g>')
    return ''.join(g)

def build(theme, data):
    T = THEMES[theme]; fs = 16; lh = 20
    x_art = 18; x_info = 500; y0 = 30
    rnd = random.Random(11)
    # ---------- rows on the right ----------
    rows = [('head', f"[ {data['name']} ] " + '/'*(WIDTH-len(data['name'])-5))]
    for k, v in data['info']:
        rows.append(('kv', k, v) if k else ('blank',))
    rows += [('blank',), ('head', section('Contact'))] + [('kv', k, v) for k, v in data['contact']]
    rows += [('blank',), ('head', section('GitHub Stats'))] + data['stats']
    h = y0 + len(rows)*lh + 10
    # ---------- timing ----------
    ROW_DT = 0.075; FRAME = 0.07; NFR = 3
    logo_top = y0 + (len(rows)*lh - len(LOGO)*lh)/2
    logo_end = len(LOGO)*ROW_DT + NFR*FRAME
    info_start = 0.35
    out = []
    # ---------- logo: decode in ----------
    logo_final = []
    for i, line in enumerate(LOGO):
        y = logo_top + i*lh; t0 = i*ROW_DT
        for f in range(NFR):
            s = scramble(line, rnd, keep=f/NFR*0.6)
            out.append(f'<text x="{x_art}" y="{y:.0f}" class="sc" style="animation-delay:{t0+f*FRAME:.3f}s">{escape(s)}</text>')
        td = t0+NFR*FRAME
        if rnd.random() < 0.22:
            logo_final.append(f'<text x="{x_art}" y="{y:.0f}" class="fi lg gl" style="animation-delay:{td:.3f}s,{logo_end+0.6+4.0+i*0.05:.3f}s,{logo_end+1.5+rnd.uniform(0,6):.2f}s">{escape(line)}</text>')
        else:
            logo_final.append(f'<text x="{x_art}" y="{y:.0f}" class="fi lg" style="animation-delay:{td:.3f}s,{logo_end+0.6+4.0+i*0.05:.3f}s">{escape(line)}</text>')
    out.append(f'<g fill="{T["art"]}">{"".join(logo_final)}</g>')
    # ---------- hacker loop on the logo (monochrome) ----------
    CW = 9.6; CYCLE = 9.0; intro_end = logo_end + 0.6
    cells = [(i, c, ch) for i, l in enumerate(LOGO) for c, ch in enumerate(l) if ch != ' ']
    # 1) random characters flicker in and out
    fk = []
    for n in range(70):
        i, c, ch = rnd.choice(cells)
        x = x_art + c*CW; y = logo_top + i*lh
        col = rnd.choice([T['art'], T['dots'], '#8a7f88'])
        fk.append(f'<g class="fk" style="animation-delay:{intro_end + rnd.uniform(0, 3.2):.2f}s;animation-duration:{rnd.uniform(2.4, 4.2):.2f}s">'
                  f'<rect x="{x-0.5:.1f}" y="{y-14:.0f}" width="{CW+1:.1f}" height="18" fill="{T["bg"]}"/>'
                  f'<text x="{x:.1f}" y="{y:.0f}" fill="{col}">{escape(rnd.choice(SCR + "0123456789abcdef"))}</text></g>')
    out.append(''.join(fk))
    # 2) every cycle the whole logo gets re-encrypted and decoded again, row by row
    for i, line in enumerate(LOGO):
        y = logo_top + i*lh; d0 = intro_end + 4.0 + i*0.05
        for f in range(NFR):
            sline = scramble(line, rnd, keep=f/NFR*0.6)
            out.append(f'<text x="{x_art}" y="{y:.0f}" class="rs" style="animation-delay:{d0 + f*FRAME:.3f}s">{escape(sline)}</text>')
    # 3) a thin scan line sweeping down the logo
    y_top = logo_top - lh; y_bot = logo_top + len(LOGO)*lh
    out.append(f'''<g class="scanbar"><rect x="{x_art-6}" y="{y_top:.0f}" width="{48*CW+12:.0f}" height="2" fill="{T['art']}" opacity="0">
<animate attributeName="y" values="{y_top:.0f};{y_bot:.0f};{y_bot:.0f}" keyTimes="0;0.45;1" dur="4s" begin="{intro_end:.2f}s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0;.55;.55;0;0" keyTimes="0;0.05;0.4;0.45;1" dur="4s" begin="{intro_end:.2f}s" repeatCount="indefinite"/></rect></g>''')
    # ---------- motto: a signal packet runs me -> you -> me (handshake) ----------
    eat_css = []; defs_m = []
    def motto_svg(k, v, y, t):
        import re as _re
        left, d, _ = kv(k, v)
        vstart = len(left) + 1 + len(d) + 1
        cm = vstart + _re.search(r'\bme\b', v).start(); cy_ = vstart + _re.search(r'\byou\b', v).start()
        xm = x_info + (cm + 1)*CW; xy = x_info + (cy_ + 1.5)*CW
        TD = intro_end + 1.2                      # the drill bores the line open
        DD = 1.5
        T0 = TD + DD + .3; C = 6.0
        xv0 = x_info + vstart*CW; xv1 = x_info + (vstart + len(v))*CW
        defs_m.append(f'<clipPath id="mclip"><rect x="0" y="{y-14}" width="{xv0:.1f}" height="20"/>'
                      f'<rect x="{xv0:.1f}" y="{y-14}" width="0" height="20"><animate attributeName="width" from="0" to="{xv1-xv0+4:.1f}" begin="{TD:.2f}s" dur="{DD}s" fill="freeze"/></rect></clipPath>')
        parts = [f'<g clip-path="url(#mclip)"><text x="{x_info}" y="{y}" class="fi" style="animation-delay:{t:.2f}s">{kv_html(k, v)}</text></g>']
        # pixel drill (original sprite): cone pointing right, spiral bands flip to look like it spins
        P = 1.7
        cone = ["####........", "#######.....", "##########..", "############", "##########..", "#######.....", "####........"]
        def drill(shift):
            px = []
            for ry, row in enumerate(cone):
                for rx, ch in enumerate(row):
                    if ch != '#': continue
                    col = T['cyan'] if (rx + ry + shift) % 4 < 2 else '#ffffff'
                    px.append(f'<rect x="{(rx+3)*P:.1f}" y="{ry*P:.1f}" width="{P+.1:.1f}" height="{P+.1:.1f}" fill="{col}"/>')
            return ''.join(px)
        body = ''.join(f'<rect x="{bx*P:.1f}" y="{by*P:.1f}" width="{P+.1:.1f}" height="{P+.1:.1f}" fill="{T["mag"] if bx == 2 else "#4a4260"}"/>' for bx in range(3) for by in range(1, 6))
        spin = (f'<g>{drill(0)}<animate attributeName="opacity" values="1;0" dur=".12s" calcMode="discrete" repeatCount="indefinite"/></g>'
                f'<g opacity="0">{drill(2)}<animate attributeName="opacity" values="0;1" dur=".12s" calcMode="discrete" repeatCount="indefinite"/></g>')
        sparks = ''.join(f'<rect x="{-4 - j*5:.0f}" y="{rnd.uniform(0, 10):.1f}" width="1.6" height="1.6" fill="{rnd.choice([T["cyan"], "#ffffff", T["mag"]])}">'
                         f'<animate attributeName="opacity" values="1;0;1" dur="{rnd.uniform(.12, .3):.2f}s" repeatCount="indefinite"/></rect>' for j in range(4))
        sprite_d = body + spin + sparks
        dy = y - 11
        # first pass: opens the line
        parts.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.02;.95;1" begin="{TD:.2f}s" dur="{DD+.25:.2f}s" fill="remove"/>'
                     f'<g><animateTransform attributeName="transform" type="translate" from="{xv0 - 20*P:.1f},{dy}" to="{xv1 + 6:.1f},{dy}" begin="{TD:.2f}s" dur="{DD+.25:.2f}s" fill="freeze"/>{sprite_d}</g></g>')
        # then it drills past again every 14 s
        CF = 14.0
        parts.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.01;.11;.12;1" begin="{TD + 9:.2f}s" dur="{CF}s" repeatCount="indefinite"/>'
                     f'<g><animateTransform attributeName="transform" type="translate" values="{xv0 - 20*P:.1f},{dy};{xv1 + 6:.1f},{dy};{xv1 + 6:.1f},{dy}" keyTimes="0;.12;1" begin="{TD + 9:.2f}s" dur="{CF}s" repeatCount="indefinite"/>{sprite_d}</g></g>')
        # glow on the two words when the packet arrives
        for col, word, xw, tarr in ((T['mag'], 'me', x_info + cm*CW, (0.0, 4.32)), (T['cyan'], 'you', x_info + cy_*CW, (1.32,))):
            vals, kts = [], []
            for ta in tarr:
                if ta > 0: kts.append(ta - .04); vals.append(0)
                kts += [ta, ta + .6]; vals += [1, 0]
            seq = sorted(zip(kts, vals))
            kt_s = '0;' + ';'.join(f'{min(.999, max(.001, tt/C)):.4f}' for tt, _ in seq if tt > 0) + ';1'
            vv = ['1' if tarr[0] == 0 else '0'] + [str(v_) for tt, v_ in seq if tt > 0] + ['0']
            parts.append(f'<text x="{xw:.1f}" y="{y}" fill="{col}" font-weight="700" opacity="0" textLength="{len(word)*CW:.1f}" lengthAdjust="spacing">{word}'
                         f'<animate attributeName="opacity" values="{";".join(vv)}" keyTimes="{kt_s}" dur="{C}s" begin="{T0:.2f}s" repeatCount="indefinite"/></text>')
        # the packet: a small glowing dot riding just under the line
        yy = y + 5
        parts.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{T0:.2f}s" dur=".01s" fill="freeze"/>'
                     f'<line x1="{xm:.1f}" y1="{yy}" x2="{xy:.1f}" y2="{yy}" stroke="{T["dots"]}" stroke-width="1" stroke-dasharray="2 3"/>'
                     f'<circle cy="{yy}" r="2.6" fill="#ffffff"><animate attributeName="cx" values="{xm:.1f};{xy:.1f};{xy:.1f};{xm:.1f};{xm:.1f}" keyTimes="0;.22;.5;.72;1" '
                     f'calcMode="spline" keySplines=".5 0 .5 1;0 0 1 1;.5 0 .5 1;0 0 1 1" dur="{C}s" begin="{T0:.2f}s" repeatCount="indefinite"/>'
                     f'<animate attributeName="fill" values="{T["mag"]};{T["cyan"]};{T["cyan"]};{T["mag"]};{T["mag"]}" keyTimes="0;.22;.5;.72;1" dur="{C}s" begin="{T0:.2f}s" repeatCount="indefinite"/></circle></g>')
        return ''.join(parts)

    # ---------- info: lines fade in, numbers decode ----------
    def kv_html(k, v, val=None):
        _, d, vv = kv(k, v)
        return f'<tspan class="pf">» </tspan><tspan class="key">{escape(k)}</tspan>:<tspan class="cc"> {d} </tspan><tspan class="value">{escape(val if val is not None else vv)}</tspan>'
    for i, r in enumerate(rows):
        y = y0 + i*lh; t = info_start + i*0.06
        if r[0] == 'blank': continue
        if r[0] == 'head':
            lab, _, rest = r[1].rpartition(' ')
            lab = lab + ' '
            body = f'<tspan class="hd">{escape(lab)}</tspan><tspan class="sl">{escape(rest)}</tspan>'
            ghost = f'{escape(lab)}'
            out.append(f'<g class="fi" style="animation-delay:{t:.2f}s">'
                       f'<text x="{x_info-2}" y="{y}" fill="{T["cyan"]}" class="rgb" style="animation-delay:{intro_end + rnd.uniform(0,5):.2f}s">{ghost}</text>'
                       f'<text x="{x_info+2}" y="{y}" fill="{T["mag"]}" class="rgb" style="animation-delay:{intro_end + rnd.uniform(0,5):.2f}s">{ghost}</text>'
                       f'<text x="{x_info}" y="{y}">{body}</text></g>'); continue
        if r[0] == 'kv' and r[1] == 'Motto':
            out.append(motto_svg(r[1], r[2], y, t)); continue
        if r[0] == 'kv':
            html = kv_html(r[1], r[2]); digits = any(c.isdigit() for c in r[2])
            if digits:
                for f in range(4):
                    out.append(f'<text x="{x_info}" y="{y}" class="sc" style="animation-delay:{t+f*0.08:.2f}s">{kv_html(r[1], r[2], scramble_digits(r[2], rnd))}</text>')
                t += 0.32
            if rnd.random() < 0.4:
                g = f'<tspan class="pf">» </tspan>{escape(r[1])}'
                dl = intro_end + rnd.uniform(0, 6)
                out.append(f'<text x="{x_info-2}" y="{y}" fill="{T["cyan"]}" class="rgb" style="animation-delay:{dl:.2f}s">{g}</text>'
                           f'<text x="{x_info+2}" y="{y}" fill="{T["mag"]}" class="rgb" style="animation-delay:{dl:.2f}s">{g}</text>')
            out.append(f'<text x="{x_info}" y="{y}" class="fi" style="animation-delay:{t:.2f}s">{html}</text>'); continue
        if r[0] == 'raw':
            for f in range(5):
                import re
                sc = re.sub(r'(class="(?:value|addColor|delColor)">)([^<]*)', lambda m: m.group(1)+scramble_digits(m.group(2), rnd), r[1])
                out.append(f'<text x="{x_info}" y="{y}" class="sc" style="animation-delay:{t+f*0.08:.2f}s">{sc}</text>')
            out.append(f'<text x="{x_info}" y="{y}" class="fi" style="animation-delay:{t+0.4:.2f}s">{r[1].replace(chr(60)+'tspan class="cc">. ', chr(60)+'tspan class="pf">» ')}</text>')
    last_y = y0 + (len(rows)-1)*lh
    end_t = info_start + len(rows)*0.06 + 0.5
    out.append(f'<text x="{x_info}" y="{last_y+lh+6}" class="fi" style="animation-delay:{end_t:.2f}s"><tspan class="pf">&gt;&gt; </tspan><tspan class="key">connection secured</tspan><tspan class="cc"> // </tspan><tspan class="value">welcome, guest </tspan><tspan class="cur">█</tspan></text>')
    h += lh
    css = f'''@font-face {{ src: local('Consolas'), local('Consolas Bold'); font-family: 'ConsolasFallback'; font-display: swap; -webkit-size-adjust: 109%; size-adjust: 109%; }}
.key {{fill: {T['key']};}} .value {{fill: {T['value']};}} .addColor {{fill: {T['add']};}} .delColor {{fill: {T['dele']};}} .cc {{fill: {T['dots']};}}
text, tspan {{white-space: pre;}}
.sc {{opacity:0; fill:{T['dots']}; animation: sc {FRAME:.2f}s linear forwards;}}
.sc .key,.sc .value,.sc .addColor,.sc .delColor {{fill:{T['dots']};}}
@keyframes sc {{ 0%,99% {{opacity:1}} 100% {{opacity:0}} }}
.fi {{opacity:0; animation: fi .01s linear forwards;}}
@keyframes fi {{ to {{opacity:1}} }}
.lg {{animation: fi .01s linear forwards, hide 9s steps(1) infinite;}}
.lg.gl {{animation: fi .01s linear forwards, hide 9s steps(1) infinite, gl 7s steps(1) infinite;}}
@keyframes hide {{ 0% {{opacity:0}} 2.4% {{opacity:1}} 100% {{opacity:1}} }}
.rs {{opacity:0; fill:{T['dots']}; animation: rs 9s steps(1) infinite;}}
@keyframes rs {{ 0% {{opacity:1}} 0.78% {{opacity:0}} 100% {{opacity:0}} }}
.fk {{opacity:0; animation-name: fk; animation-timing-function: steps(1); animation-iteration-count: infinite;}}
@keyframes fk {{ 0% {{opacity:1}} 4% {{opacity:0}} 100% {{opacity:0}} }}
@keyframes gl {{ 0%,90%,100% {{transform:translateX(0)}} 91% {{transform:translateX(7px)}} 92.5% {{transform:translateX(-5px)}} 94% {{transform:translateX(0)}} }}
.cur {{fill:{T['mag']}; animation: bl 1s steps(1) infinite;}}
.pf {{fill:{T['mag']};}}
.gb {{animation: gb 8s steps(1) infinite;}}
@keyframes gb {{ 0%,100% {{transform:translateX(0)}} 4% {{transform:translateX(18px)}} 6% {{transform:translateX(-10px)}} 8% {{transform:translateX(0)}} }}
.jc {{animation: jc .3s steps(1) infinite;}} .jo {{animation: jo .3s steps(1) infinite;}}
@keyframes jc {{ 0% {{opacity:1}} 50% {{opacity:0}} }} @keyframes jo {{ 0% {{opacity:0}} 50% {{opacity:1}} }}
{chr(10).join(eat_css)}
.hd {{fill:{T['value']}; font-weight:700;}}
.sl {{fill:{T['dots']};}}
.rgb {{opacity:0; animation: rgb 6s steps(1) infinite;}}
@keyframes rgb {{ 0% {{opacity:.85}} 1.6% {{opacity:0}} 2.4% {{opacity:.85}} 3.2% {{opacity:0}} 100% {{opacity:0}} }}
@keyframes bl {{ 50% {{opacity:0}} }}
@media (prefers-reduced-motion: reduce) {{ .sc {{display:none}} .fi,.gl {{opacity:1; animation:none}} .fk,.rs,.scanbar,.rgb {{display:none}} .gb {{animation:none}} .eat {{animation:none!important; opacity:1}} .lg {{animation:none; opacity:1}} .cur {{animation:none}} }}'''
    return f'''<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" font-family="ConsolasFallback,Consolas,'DejaVu Sans Mono',monospace" width="1075px" height="{h}px" font-size="{fs}px">
<style>{css}</style>
<defs>{"".join(defs_m)}<radialGradient id="vig" cx="50%" cy="45%" r="75%"><stop offset="0" stop-color="#1a0b10" stop-opacity=".55"/><stop offset=".6" stop-color="#050406" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".7"/></radialGradient>
<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#ffffff" opacity=".022"/></pattern></defs>
<rect width="1075px" height="{h}px" fill="{T['bg']}" rx="15"/>
{background(h, logo_top, T)}
<rect width="1075px" height="{h}px" fill="url(#vig)" rx="15"/>
<rect x=".5" y=".5" width="1074" height="{h-1}" fill="none" stroke="#24161c" rx="15"/>
<g fill="{T['text']}">{"".join(out)}</g>
<rect width="1075px" height="{h}px" fill="url(#scan)" rx="15" pointer-events="none"/>
</svg>'''


def render(s, today):
    data = dict(name='benji@void',
  info=[('OS','Windows, Kali Linux, Arch Linux'),
        ('Uptime', age(datetime.date(2023,5,17), today)),
        ('Mobile','Android, iOS'),
        ('Location','Surabaya, Indonesia'),
        ('Role','Co-owner & System Developer'),
        (None,None),
        ('Languages.Programming','Python, JS, C#, Dart, SQL'),
        ('Languages.Learning','Java (Minecraft mod)'),
        ('Stack.Backend','Node.js, Express, MySQL'),
        ('Stack.Mobile','Flutter'),
        ('Stack.Automation','Python, Apps Script, GH Actions'),
        ('Stack.APIs','Sheets, Search Console, WA gateway'),
        ('Stack.AI','Claude Code, OCR, AI agents'),
        ('Stack.Infra','Linux VPS, Traccar, cron jobs'),
        ('Stack.Gamedev','Unity (C#), physics simulation'),
        ('Stack.Reversing','Ghidra, IL2CPP teardown'),
        (None,None),
        ('Now.Building','booking system w/ OCR'),
        ('Now.Shipping','ops app for field staff'),
        (None,None),
        ('Hobbies.Software','After Effects, Blender'),
        ('Hobbies.Modding','BBS × Epic Fight, Forge'),
        ('Motto','believe in me, who believes in you')],
  contact=[('Instagram','@444xbnji'),('GitHub','BenjiJimaa')],
  stats=stat_rows(s)
)
    return build('dark', data)
