#!/usr/bin/env python3
"""Render the animated SVG sections of the BenjiJimaa profile README.

Runs daily in GitHub Actions. Contribution data comes from the GitHub GraphQL API
(GITHUB_TOKEN); without a token it falls back to sample data so the script can be
tested locally.
"""
import os, json, math, random, datetime, urllib.request
from html import escape

USER = os.environ.get("PROFILE_USER", "BenjiJimaa")
OUT = os.environ.get("OUT_DIR", "dist")
os.makedirs(OUT, exist_ok=True)

# ---- palette (Blood) ------------------------------------------------------
C = dict(bg="#07060b", panel="#0d0b13", panel2="#13101c", line="#251f33",
         text="#ddd8ea", dim="#7a7090", faint="#4a4260",
         field="#b8261a", fieldhot="#ff8a6a", edge="#ff5a3c", fur="#3a1d20",
         eye="#ff7a3a", maw="#a3161f", tongue="#ff8c96", fang="#fff0c8",
         acid="#9dff4a", cyan="#22e6ff", hot="#ff3b2a")
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace"
W = 860  # every card shares this width

def esc(s):
    return escape(s, quote=False)

def svg_doc(w, h, body, extra_css=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">
<style>
text{{font-family:{MONO};white-space:pre}}
.d{{fill:{C['dim']}}} .t{{fill:{C['text']}}} .p{{fill:{C['edge']}}} .c{{fill:{C['cyan']}}} .a{{fill:{C['acid']}}} .e{{fill:{C['eye']}}}
.blink{{animation:blink 1s steps(1) infinite}} @keyframes blink{{50%{{opacity:0}}}}
{extra_css}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
</style>
{body}
</svg>'''

def window(w, h, title, body, mon=""):
    """Terminal window frame. Content area starts at y=36."""
    m = f'<text x="{w-16}" y="21" text-anchor="end" font-size="12" fill="{C["hot"]}">{esc(mon)}</text>' if mon else ""
    return f'''<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="8" fill="{C['panel']}" stroke="{C['line']}"/>
<path d="M1 28.5 H{w-1}" stroke="{C['line']}"/>
<circle cx="18" cy="14.5" r="5" fill="{C['hot']}"/><circle cx="34" cy="14.5" r="5" fill="{C['faint']}"/><circle cx="50" cy="14.5" r="5" fill="{C['faint']}"/>
<text x="66" y="19" font-size="12" class="d">{esc(title)}</text>{m}
{body}'''

def line(x, y, runs, size=13, cols=None, cw=None):
    """runs: list of (cls_or_color, text). Optional fixed width via textLength."""
    parts = []
    for k, s in runs:
        if not s: continue
        attr = f'fill="{k}"' if k.startswith('#') else f'class="{k}"'
        parts.append(f'<tspan {attr}>{esc(s)}</tspan>')
    tl = ''
    if cols and cw:
        tl = f' textLength="{cols*cw:.1f}" lengthAdjust="spacingAndGlyphs"'
    return f'<text x="{x}" y="{y}" font-size="{size}"{tl}>{"".join(parts)}</text>'

def pline(x, y, user="benji", host="void", fs=13, cw=7.8):
    n = len(f"{user}@{host}:~$ ")
    return line(x, y, prompt(user, host), fs, n, cw)

def prompt(user="benji", host="void"):
    return [("p", f"{user}@{host}"), ("d", ":"), ("c", "~"), ("d", "$ ")]

# ---- contribution data ----------------------------------------------------
def gql(query, variables):
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok: return None
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {tok}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def fetch_days():
    q1 = "query($u:String!){user(login:$u){createdAt contributionsCollection{contributionYears}}}"
    q2 = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){
      restrictedContributionsCount contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""
    try:
        r = gql(q1, {"u": USER})
        if not r or "errors" in r: raise RuntimeError(r)
        years = r["data"]["user"]["contributionsCollection"]["contributionYears"]
        days = {}
        for y in sorted(years):
            rr = gql(q2, {"u": USER, "f": f"{y}-01-01T00:00:00Z", "t": f"{y}-12-31T23:59:59Z"})
            cc = rr["data"]["user"]["contributionsCollection"]
            for wk in cc["contributionCalendar"]["weeks"]:
                for d in wk["contributionDays"]:
                    days[d["date"]] = (d["contributionCount"], d["contributionLevel"])
            print("year", y, "calendar", cc["contributionCalendar"]["totalContributions"], "restricted", cc["restrictedContributionsCount"])
        # last-year calendar (as shown on the profile)
        rr = gql("""query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
          weeks{contributionDays{date contributionCount contributionLevel weekday}}}}}}""", {"u": USER})
        weeks = rr["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        return days, weeks, True
    except Exception as e:
        if os.environ.get("CI"):
            raise SystemExit(f"could not fetch contribution data: {e}")
        print("using sample data:", e)
    # sample data for local tests
    random.seed(4)
    today = datetime.date.today(); days = {}; weeks = []
    start = today - datetime.timedelta(days=364 + (today.weekday()+1) % 7)
    for w in range(53):
        wk = []
        for d in range(7):
            dt = start + datetime.timedelta(days=w*7+d)
            if dt > today: break
            n = random.choice([0]*28 + [1, 2, 3, 5])
            lvl = "NONE" if n == 0 else ["FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"][min(3, n-1)]
            wk.append({"date": dt.isoformat(), "contributionCount": n, "contributionLevel": lvl, "weekday": d})
            days[dt.isoformat()] = (n, lvl)
        weeks.append({"contributionDays": wk})
    return days, weeks, False

def stats(days):
    ds = sorted(days)
    total = sum(days[d][0] for d in ds)
    first = next((d for d in ds if days[d][0] > 0), ds[0] if ds else "")
    best = (0, None, None); cur = 0; cs = None
    for d in ds:
        if days[d][0] > 0:
            if cur == 0: cs = d
            cur += 1
            if cur > best[0]: best = (cur, cs, d)
        else:
            cur = 0
    # current streak: count back from today (today may still be empty)
    today = datetime.date.today()
    k = 0; dt = today
    if days.get(dt.isoformat(), (0,))[0] == 0: dt -= datetime.timedelta(days=1)
    while days.get(dt.isoformat(), (0,))[0] > 0:
        k += 1; dt -= datetime.timedelta(days=1)
    return dict(total=total, since=first, cur=k, best=best[0], best_from=best[1], best_to=best[2])

# ---- 1. hero cat ----------------------------------------------------------
CAT = {"k": ["ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "ffffffffffffffffffffhuuhhhffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "fffffffffffffffffffhuuuuuuhhffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "fffffffffffffffffffhuuuuuuuuhfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "fffffffffffffffffffhuuuuuuuuuuhfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "fffffffffffffffffffhuuuuuuuuuuuhffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "fffffffffffffffffffhuuuuuuuuuuuuhfffffffffffffffffffffffffffffffffffffffffffffhhhhhfffffffffffffffffffff", "fffffffffffffffffffhuuuuuuuuuuuuuhhffffffffffffffffffffffffffffffffffffffffhhhuuuuuhffffffffffffffffffff", "fffffffffffffffffffhuuuuuuuuuuuuuuuhfffffffffffffffffffffffffffffffffffffhhuuuuuuuhfffffffffffffffffffff", "fffffffffffffffffffhuuuuuuuuuuuuuuuuhhffffffffffffffffffffffffffffffffhhhuuuuuuuuuhfffffffffffffffffffff", "ffffffffffffffffffffuuuuuuuuuuuuuuuuuuhhfffffffffffffffffffffffffffhhuuuuuuuuuuuuhffffffffffffffffffffff", "ffffffffffffffffffffhuuuuuuuuuuuuuuuuuuuhhhhhhhhhhhhhhhhfffffffhhhuuuuuuuuuuuuuuhfffffffffffffffffffffff", "ffffffffffffffffffffhuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhhhhhuuuuuuuuuuuuuuuuuhffffffffffffffffffffffff", "fffffffffffffffffffffhuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffff", "fffffffffffffffffffffhuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffff", "fffffffffffffffffffffuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhffffffffffffffffffffffffff", "fffffffffffffffffffffuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffffff", "ffffffffffffffffffffhuuuuuuuuuuuuuuuuuueeeeeeeuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhhfffffffffffffffffffffffffff", "fffffffffffffffffffhhuuuuuuuuuuuuuuuuuueeeeeeeeuuuuuuuuuuuuuuuuuuuuuuuuuuuufffffffffffffffffffffffffffff", "ffffffffffffffffffhuuuuuuuuuuuuuuuuuuuuuuuuueeeeuuuuuuuuuuuuuuuueeeeeuuuuuufffffffffffffffffffffffffffff", "ffffffffffffffffffuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuueeeeeeeeuuuuhffffffffffffffffffffffffffff", "fffffffffffffffffhuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuueeeeeeeuuuuuhhffffffffffffffffffffffffff", "ffffffffffffffffhuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuffffffffffffffffffffffffff", "fffffffffffffffhuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffff", "fffffffffffffffhuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffff", "fffffffffffffffhuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffff", "ffffffffffffffhhuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaaaaaaaauuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffff", "fffffffffffhhhuuuuuuuuuuuuuuuuuuuuuuuuuaaaaaaaaaaaaaaagaaaaaaaaauuuuuuuuuuuuuuffffffffffffffffffffffffff", "uuuuhhhhhhhuuuuuuuuuuuuuuuuuuuuuuuuuuaaaaagaaggaaaggaaaaaaaagaoaaauuuuuuuuuuuhffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaaaaaaaaaaaaaagaaaaaaaaaaggaaaauuuuuuuuhhfffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaaaaaaaaaaaaaaagaaaaaaaaaaagaaauuuuuuuuhfffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaauuuuuuuuhffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaaaaaaaaooaaaoaaaaaaaaaaaaaaauuuuuuuuhfffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaaggaaoooaaaoaaaaoaaaaaaaauuuuuuuuhfffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaaggooooaaooaoaoogggaaauuuuuuuuuhffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaaggoooaaooaaoaaogaaauuuuuuuuuuhfffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaagooaaooaaaoaaaaaauuuuuuuuuhhffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaagoaaaoaaaaaaaaaauuuuuuuuhhffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaaaaaaoaaaaaaaaauuuuuuhhffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaaoaaaaaaaaaoauuuuuuhfffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaoooaaaaaooauuuuuhfffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaaooooaaooouuuuuhffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuagaooooagguuuuhfffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuaggguuuuuuhhfffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhhffffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhffffffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhffffffffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuufffffffffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhffffffffffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhffffffffffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuhfffffffffffffffffffffffffffffffffffffffffffffffffffffffff"], "c": ["b50e215e 532c36d8c101f73 6620f6c24141c 12 bc0a3e291d727cb9855 0ec0 482924c58f14276ecf80d2973ff10ef12d215", "0ff2aec 374712062868 3d8a781bc 9 adfc2ee5150b4 e cada3060 25cc4b8c500d 8e74b1b53a46d1 fbcd65 b750a56a4cc", "7146c41 953f8b6e30395d b5066e2d54d6 da9d3b7b2 53a026   000385 9d ffa ef2af4 d30e285aeb5aa2a981fd9e63299e", "5835b6668c845cf3caa720e e08a2653405c8f448390f b 502cf169d66215838812 0  51b44ea ff f4fba34b8886cca61a2e ", "b05e1e8 13c29051d90d^  .?M6c 2f6 cb 996ab52e6 7bb 306c138eb190 90eb3 4a2103a15 c6805e0f2208c2035576 af 6", "9fb 3b94fb4203cd736F ,    'M 2fb fb4f6d54e40d4 d603e7   c 22cca3eabc 7ad 5 15a 201e77ee2acfc29e25dbac931", "3ed68e85636dafa2d49L        ?c 82 c7936  c 7ce1 c920 3    401d5813 9185bfc3fa2be3c5e42a e c5 85  f0bb054", "c92fc71cb2e58 c5a3 L          X8a89 b0e5 8 a412260c3 0b2ab 7f8 8f7b d62 f5a2af16252996 6e571 6 ea703f41b", "86fe87ccbf 0e5e90 5L      .    ?e fa2  5   f0  7  95 d59d19f5 e5ea0a972c 7b a2c9 7a4b 7eb5bb6e0a161e21f5", "4ac  fe11a66b d6 b5L     ,      ?8bad ebfe41  89a6c  e33a3 9b791 7 0 97b 56c4 P'''M2ff19f7f 93 2fa620ef4", "f463f8e8c390ed9c 3fL           . .898e7 90d05 5c6e5ad9b  d15 d33    22 7234MF.     32c  8da35b57bc 5293e", "1ade8ce22a7 a6 5533E               ?292f453c4d09  1 5d 49c9a45 6  59c603cP'       _ab  5a6b409 ec40 29f8", "f1ab7f55bcf b2f620eE              , '81 aa5352 7f 2 2  550a1a502893723P^.         ge8e3  9ef4 f59dd8b18a", " 995453ea0518 b 60                    '99d  40 e6417da 40548   c45eP^            u0fe24451f10c 9f112c825", "641fc 82b 9e0eea742a_            .      'TT**T*TTT****MM 34 5 9PP'       ,      _66db6f8ce 9f435 5787e4b", "9135410977 219f88529g                   ' '              ...''             ,, ,_  338850fb08a4e8f9 d68b8", "5fd2936dafa244dd5b75 _                                                        _8df3 ece254191 8837 49e41", "4727c01c86  7 1f 0839_                                                        g8c9f9d8 cf7ca 9f26292e09f", "5856 e27 7cd1e3 ba4c0                         ,                              u670a7d98cd5237a64d b8b8bdd", "8d197 0 f9d2c7452e2b9  ,     '                           ,                  _ e79d 326 29009a4e6fd94b4f5", "8c510d 8dbb94fc6f657F.         ,  .    __ggg__                             ,@50 647528d27 9c8d8d  cd6480", "0f 29d6fa 874bdde89F.                  'TMBBBBg               .     '      7562b b57529a 9ed7a09e 7c14f3", "31eabd4784  ef 23 F.         ,  ,        , '.?*'           ,    ,ggg,      2 4d68 59d a17c0 4dd4ced4cf 0", "3 bb35b0c14691 50b                     .  ,                   .3BBBBBg_    ?be41 9ba624 057  9e1c  cf61b", "643eccf8b3ad65 7fC                                 '  .     ' , .''TTTT     .M8  a5 51c9c  a 4590ccc 718", "6289cf6f6c  9e  .  .                       ,'                        '       ,7  9557a 6d83e280a e5857d8", "9fc6d1fd7a0  ffL                                        .                     3 482601b1f46f333fdeb634bb", "1561 fd5 53c17 L    ,                                              .'         q59 f44 1c 9 6875 9 25f 6e", "10942586a5e46c L            '                 '                      .        3e   621f2cd90ff529 96446d", "40ffbe70ce6eb P.                                   ______gg_                  3c  d7  72 8cd0c 32219 fa2", "52132 d81 dPF'                         _ggggg@@MBPF3$BgPB&$B@gg_              4 3f 20594ee5b d bf9a 84f8", "    ..'TT'.         .                g@gggBggWp@&EBF%%W@g@ggTLM3B_           g2  5 8c74 6  6 a3b85ef9da6", "                                   _@@@###B&#BgSQMB3PB$$#%&%&3B8&#L        _gac0020 4163 e32  45c5ca6256", "        .       .           .     g#&&8$U$&%N@&%&%8@#@%&&%&#%LF#$F        _9 8a 5034 ebc9c9f8867894ce7 2", "                           '      3$$%%%LB$E@##%&$&%$%%%$&M#&&$$C        ge752ab9 ba 5 0  97229118d 0e1f", "                                  .B&%F3$L?gE##$q3M&%BF8&E?#$#P.        g 85922 193604b9e22d690345e9f5bf", "     ,                             3%EE]&Lg=*8%#@8H#E~3BMF@#B'        _  74 5a2d2a223ad2ba27594f06a cbb8", "         ,                       '  3&gWFg***&M@*8E$3=yC8#B'         _7ce0859 35ac6e b07aaf3b03 2 7453f0", "  ,                                 .8&%{=~B@K@H@%B3EEPgB^      .   g240103de17a1 a4cd5a5bb78f c0b1abcd5", "    .                     ,      ,   3%gF@P#$~K#B%3]$hg&'    .    _@f e22  7 0808d 83b3d38 fc6de 9c14619", "          '        .       ,   '      3%R?&#%88%$$E8$W$F        _g9   1e4 a256d50bc 8445fe2e11be5f6f3fd0", "                                  '    9$L8%&g8&&Eg&%$F.      _gc   2 262f f2f67 d 9f52 be  67ca82bdd324", "                          .         '  '%E@8&%%#&#$BpF      g   0 c 1c 012 ff9af6c fc4e00 628 aebfe81cff", "          '     .  '       .            ^B%@gB@%%B@B!     _a0 9b2d9d408636 948c 508ab60 c612bf39d 401f50", "                                    ,    3B8B~EBFBP.     _ e73 291 471a546 a   b0cb1575f590806a25f870d82", "  '   ..                                . ?WFTTWF{un '  _ 2 7509c62 a62b770a64629d  59 6 1bbda 7c2b1c3d3", "                         .                   .'''      _@dcb9fd8c878f 96e3 7  1fbe5258a2d10ff0963d7ee2c ", "                           ,                          _@a5 0 71c890da4c3f67cabe6 74d0a1 ff37f 3339f19c94", "                   .     '       .                    @bc6904 15f74226e7 41974a2f9b69724842cf7c193 94c4a", "  ,         ' .                           ,          @ 55   e 6 a6c5da612d90e76b6574e 13591e47a00f051568", "                                                    g1a00a a187  7d 13 a 1e707f700dc9ccd33dd3a25b0a6c30f", "                            . .                  , ud19f9  b58d9 c8 bb21b17 63f94101eaa8c831c5139 a05 f7", "                   .                                 c da6 9a2  4a 93c5100cf60 cee635efdc8b6cb2e62bf90b ", "                      ,                       .   3 4ba 219b2dbca 4253f8b4193b3314b aaf41bab ccfbf70d6b8", "     .                        '            '   . _88831f5a0 c0bd5 291599b6 72465216 8d6238495c c72c584b5", "                          .    .    ,    .       @ e97eb3d363 3 90  83953a3c093d d0f30fd408eb59cbaeb535b", "                    ,             '             @871e733420eb0a13d29b9d326e55b 5 678 c2c24d9aceb e49 53c", "                 '            .                31a4380bc1e49b9053100dab8d8e89a5c25bb4dee7213bbc0bc3 e c2", "      '                                       _a27a5bac8c382 0 ab22d164a97f91f1e865d4ce5df8e9239b5e7cbce"]}

def build_cat():
    rows_k, rows_c = CAT["k"], CAT["c"]
    R, COLS = len(rows_k), len(rows_k[0])
    cw, lh, fs = 7.75, 12.6, 12.4
    pad = (W - COLS*cw) / 2
    top = 40
    h = int(top + R*lh + 22)
    col = dict(f=C['field'], h=C['edge'], u=C['fur'], e=C['eye'], a=C['maw'], o=C['tongue'], g=C['fang'])
    rnd = random.Random(7)
    base, eyes, hot = [], [], [[] for _ in range(4)]
    for r in range(R):
        y = top + (r+1)*lh
        runs = []; erun = []
        for i, (k, ch) in enumerate(zip(rows_k[r], rows_c[r])):
            if k == 'e':
                runs.append(('#00000000', ' ')); erun.append((col['e'], ch))
            else:
                runs.append((col[k], ch)); erun.append(('#00000000', ' '))
            if k == 'f' and ch != ' ' and rnd.random() < 0.05:
                layer = hot[rnd.randrange(4)]
                layer.append((r, i, rnd.choice('0123456789abcdef')))
        # merge runs of same color
        m = []
        for k2, ch in runs:
            if m and m[-1][0] == k2: m[-1] = (k2, m[-1][1]+ch)
            else: m.append((k2, ch))
        glitch = rnd.random() < 0.18
        g_cls = f' class="gl gl{rnd.randrange(3)}"' if glitch else ''
        base.append(f'<g{g_cls}>{line(f"{pad:.1f}", f"{y:.1f}", m, fs, COLS, cw)}</g>')
        if any(k == 'e' for k in rows_k[r]):
            em = []
            for k2, ch in erun:
                if em and em[-1][0] == k2: em[-1] = (k2, em[-1][1]+ch)
                else: em.append((k2, ch))
            eyes.append(line(f"{pad:.1f}", f"{y:.1f}", em, fs, COLS, cw))
    hot_svg = []
    for li, layer in enumerate(hot):
        t = ''.join(f'<text x="{pad + i*cw:.1f}" y="{top+(r+1)*lh:.1f}" font-size="{fs}" fill="{C["fieldhot"]}">{ch}</text>' for r, i, ch in layer)
        hot_svg.append(f'<g class="hot hot{li}">{t}</g>')
    css = f'''
.hot{{opacity:0;animation:flick 2.4s steps(1) infinite}}
.hot1{{animation-delay:.6s}} .hot2{{animation-delay:1.2s}} .hot3{{animation-delay:1.8s}}
@keyframes flick{{0%{{opacity:1}}25%{{opacity:0}}}}
.gl{{animation:gl 5s steps(1) infinite}} .gl1{{animation-delay:1.7s}} .gl2{{animation-delay:3.3s}}
@keyframes gl{{0%{{transform:translateX(0)}}92%{{transform:translateX(9px)}}94%{{transform:translateX(-7px)}}96%{{transform:translateX(0)}}}}
.eyes{{animation:eb 4.2s infinite}}
@keyframes eb{{0%,93%,100%{{opacity:1}}95%{{opacity:0}}}}'''
    body = f'''<rect width="{W}" height="{h}" rx="8" fill="#050408" stroke="{C['line']}"/>
<defs><pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#ffffff" opacity=".035"/></pattern>
<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<pattern id="haz" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="7" height="14" fill="{C['hot']}" opacity=".08"/></pattern></defs>
<rect x="1" y="1" width="{W-2}" height="27" rx="7" fill="url(#haz)"/><path d="M1 28.5 H{W-1}" stroke="{C['line']}"/>
<text x="14" y="19" font-size="12" fill="{C['hot']}" letter-spacing="1.5">[!] HOSTILE ENTITY DETECTED // DO NOT PET</text>
<text x="{W-14}" y="19" font-size="12" text-anchor="end" class="d">pid 0x6b3n7</text>
{''.join(base)}
{''.join(hot_svg)}
<g class="eyes" filter="url(#glow)">{''.join(eyes)}</g>
<rect width="{W}" height="{h}" rx="8" fill="url(#scan)" pointer-events="none"/>'''
    return svg_doc(W, h, body, css)

# ---- 2. terminal header ---------------------------------------------------
FIG_CAT = ["██╗    ██╗", "███╗  ███║", "█████████║", "██▀███▀██║", "█████████║", "╚════════╝"]
FIG = ["██████╗ ███████╗███╗   ██╗     ██╗██╗",
       "██╔══██╗██╔════╝████╗  ██║     ██║██║",
       "██████╔╝█████╗  ██╔██╗ ██║     ██║██║",
       "██╔══██╗██╔══╝  ██║╚██╗██║██   ██║██║",
       "██████╔╝███████╗██║ ╚████║╚█████╔╝██║",
       "╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚════╝ ╚═╝"]

def typing_lines(x, y, lines, total, fs=13, cw=7.8):
    """Each line types in, holds, then clears; lines take turns over `total` seconds."""
    out = []; slot = total / len(lines)
    for i, s in enumerate(lines):
        n = len(s); full = n*cw + 2
        keys = [0.0]; vals = [0.0]
        t0 = i*slot/total; tt = 0.06*len(s)/total  # typing speed 60ms/char
        steps = max(1, n)
        for k in range(1, steps+1):
            keys.append(min(1, t0 + tt*k/steps)); vals.append(min(full, k*cw+1))
        keys.append(min(1, t0 + (slot-0.4)/total)); vals.append(full)
        keys.append(min(1, t0 + slot/total)); vals.append(0)
        if keys[1] > 0: keys.insert(1, t0); vals.insert(1, 0)
        # normalize monotonic & end at 1
        pairs = sorted(set(zip(keys, vals)), key=lambda p: (p[0], -p[1] if p[0] < 1 else p[1]))
        ks, vs = [], []
        for k_, v_ in pairs:
            if ks and abs(k_-ks[-1]) < 1e-6: vs[-1] = v_; continue
            ks.append(k_); vs.append(v_)
        if ks[-1] < 1: ks.append(1.0); vs.append(0)
        ks[0] = 0.0
        cid = f"ty{i}"
        out.append(f'''<clipPath id="{cid}"><rect x="{x}" y="{y-fs}" height="{fs+6}" width="0">
<animate attributeName="width" dur="{total}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{';'.join(f'{k:.4f}' for k in ks)}" values="{';'.join(f'{v:.1f}' for v in vs)}"/></rect></clipPath>
<text x="{x}" y="{y}" font-size="{fs}" class="a" clip-path="url(#{cid})">{esc(s)}</text>''')
    return ''.join(out)

def build_header():
    h = 236; cw = 7.8; fs = 13
    lines = ['echo "nocturnal dev // codes after midnight"', 'sudo rm -rf /bugs',
             'echo "404: mercy not found"', 'kill -9 $(pgrep sleep)']
    fig_rows = []
    for i in range(6):
        catp, txt = FIG_CAT[i], FIG[i]
        runs = []
        for ch in catp + "  " + txt:
            k = C['edge'] if ch == '█' else (C['eye'] if ch == '▀' else (C['maw'] if ch.strip() else '#00000000'))
            if runs and runs[-1][0] == k: runs[-1] = (k, runs[-1][1]+ch)
            else: runs.append((k, ch))
        fig_rows.append(line(22, 84 + i*18, runs, 17, len(catp)+2+len(txt), 10.6))
    plen = len("benji@void:~$ ")
    body = window(W, h, "benji@void: ~", f'''
{line(22, 56, prompt() + [("t", 'figlet -f "ANSI Shadow" benji')], fs)}
<g filter="url(#g2)" class="fg">{''.join(fig_rows)}</g>
{line(22, 196, [("d", "uid=1000(benji) gid=1000(goth) groups=1000(goth),27(sudo),666(void)")], 12)}
{pline(22, 220)}
{typing_lines(22 + plen*cw, 220, lines, 16, fs, cw)}
''', mon="武蔵")
    defs = f'<defs><filter id="g2" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
    css = '.fg{animation:fg 6s steps(1) infinite} @keyframes fg{0%{transform:translateX(0)}90%{transform:translateX(6px)}92%{transform:translateX(-4px)}94%{transform:translateX(0)}}'
    return svg_doc(W, h, defs + body, css)

# ---- 3. whoami + dokkodo --------------------------------------------------
def build_whoami():
    fs = 13; lh = 19; x = 104
    who = [
        prompt() + [("t", "whoami --verbose")],
        [("d", "name       "), ("t", "Benji "), ("d", "(he/him)")],
        [("d", "based in   "), ("t", "Surabaya, Indonesia "), ("d", "· UTC+7")],
        [("d", "role       "), ("t", "backend & automation engineer")],
        [("d", "building   "), ("t", "booking & fleet platform · internal ops app · REST APIs")],
        [("d", "side quest "), ("t", "motion design & VFX edits "), ("d", "(After Effects)")],
        [("d", "dojo       "), ("a", "二天一流 Niten Ichi-ryū"), ("d", " · two blades: code & craft")],
        [("d", "motto      "), ("a", '"pakek dah pakek"')],
        [],
        prompt() + [("t", "cat ~/.dokkodo")],
        [("d", "# the way of walking alone, ported to the terminal")],
        [("p", "01  "), ("t", "accept the bug as it is, then fix it.")],
        [("p", "02  "), ("t", "never depend on one weapon. learn the whole stack.")],
        [("p", "03  "), ("t", "think lightly of yourself, deeply of the system.")],
        [("p", "04  "), ("t", "no regrets about past commits. refactor forward.")],
        [("p", "05  "), ("t", "train every day. the way is in the practice.")],
        [("d", "                                         — after 宮本武蔵, 1645")],
    ]
    h = 36 + len(who)*lh + 40
    rows = ''.join(line(x, 60 + i*lh, r, fs) for i, r in enumerate(who) if r)
    cur = f'<text x="{x + 14*7.8:.1f}" y="{60+len(who)*lh}" font-size="{fs}" class="t blink">█</text>'
    kanji = ''.join(f'<text x="50" y="{100 + i*64}" font-size="54" text-anchor="middle" fill="{C["hot"]}" opacity=".9" font-family="\'Yu Mincho\',\'Hiragino Mincho ProN\',\'Noto Serif CJK JP\',serif">{ch}</text>' for i, ch in enumerate("二天一流"))
    body = window(W, h, "benji@void: ~/whoami", f'''
<g filter="url(#kg)">{kanji}</g>
<path d="M88 44 V{h-14}" stroke="{C['line']}"/>
{rows}
{line(x, 60+len(who)*lh, prompt(), fs)}{cur}''')
    defs = f'<defs><filter id="kg"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
    return svg_doc(W, h, defs + body)

# ---- 4. ps aux ------------------------------------------------------------
PROCS = [  # pid, stat, cpu base, jitter, name, ext, note
    (1337, "R", 87, 9, "artrent-api", "", "# REST API rental mobil, aktif"),
    (2077, "S+", 12, 6, "minecraft-mod", ".java", "# spawning ..."),
    (404, "Z", 0, 0, "product-ai-agent", "", "<defunct>"),
    (418, "Z", 0, 0, "id-categories-auto", "", "<defunct>"),
    (500, "Z", 0, 0, "insight-error-handler", "", "<defunct>"),
    (666, "I", .1, 0, "convert-png-to-webp", "", "# idle, masih kepakai"),
    (777, "I", .1, 0, "generate-folder-auto", "", "# idle, masih kepakai"),
    (808, "I", 0, 0, "express-crud", "", "# idle"),
]
def build_ps():
    fs = 13; lh = 20; cw = 7.8; x = 22
    h = 36 + (len(PROCS)+5)*lh + 18
    stc = {"R": C['acid'], "S+": C['cyan'], "I": C['dim'], "Z": C['eye']}
    out = [line(x, 58, prompt() + [("t", "ps aux | grep projects  "), ("d", "· refresh 1.0s")], fs),
           line(x, 58+lh, [("d", "  PID  STAT  %CPU  COMMAND")], fs)]
    rnd = random.Random(3)
    for i, (pid, st, b, j, name, ext, note) in enumerate(PROCS):
        y = 58 + (i+2)*lh
        cls = ' class="blink"' if st == "R" else ''
        out.append(f'<text x="{x}" y="{y}" font-size="{fs}"><tspan class="d">{pid:>5}  </tspan><tspan fill="{stc[st]}"{cls}>{st:<4}</tspan></text>')
        cx = x + 13*cw
        if j:
            vals = [b + rnd.uniform(-j, j) for _ in range(6)]
            for k, v in enumerate(vals):
                out.append(f'<text x="{cx}" y="{y}" font-size="{fs}" class="t cpu" style="animation-delay:{k}s">{v:4.1f}</text>')
        else:
            out.append(f'<text x="{cx}" y="{y}" font-size="{fs}" class="t">{b:4.1f}</text>')
        nx = x + 19*cw
        if st == "Z":
            out.append(f'<text x="{nx}" y="{y}" font-size="{fs}" class="d">{esc(name)}</text>')
            out.append(f'<path d="M{nx} {y-4.5} h{len(name)*cw}" stroke="{C["maw"]}" stroke-width="1.4"/>')
        else:
            out.append(f'<text x="{nx}" y="{y}" font-size="{fs}" class="t">{esc(name)}</text>')
        ex = nx + (len(name)+1)*cw
        if ext:
            out.append(f'<rect x="{ex-2}" y="{y-11}" width="{len(ext)*cw*0.85+6}" height="14" rx="2" fill="none" stroke="#e2762f"/><text x="{ex+1}" y="{y-0.5}" font-size="11" fill="#e2762f">{ext}</text>')
        out.append(f'<text x="{x + 43*cw}" y="{y}" font-size="{fs}" class="d">{esc(note)}</text>')
    y = 58 + (len(PROCS)+3)*lh
    out.append(line(x, y, [("d", "STAT: "), ("a", "R"), ("d", " running · "), ("c", "S+"), ("d", " starting · "),
                           ("d", "I idle · "), ("e", "Z"), ("d", " zombie (mangkrak, tapi nggak dibunuh)")], 12))
    css = '.cpu{opacity:0;animation:cpu 6s steps(1) infinite} @keyframes cpu{0%{opacity:1}16.66%{opacity:0}}'
    return svg_doc(W, h, window(W, h, "benji@void: ~/projects", ''.join(out)), css)

# ---- 5. tree + proc -------------------------------------------------------
TREE = [("lang/", "</>", [("python", ".py", "#3d7ab8"), ("javascript", ".js", "#e8c33b"), ("dart", ".dart", "#2bb5e8"), ("java", ".java", "#e2762f")]),
        ("backend/", "⛁", [("node.js", ".mjs", "#6aa84f"), ("express", ".js", "#a8a8b3"), ("mysql", ".sql", "#4c8fbf")]),
        ("mobile/", "▯", [("flutter", ".dart", "#46c3f2")]),
        ("automation/", "⚙", [("google-apps-script", ".gs", "#f4b400")]),
        ("tools/", "⚒", [("git", ".git", "#f05033"), ("after-effects", ".aep", "#9a8cff")])]
HALF = 424

def build_tree():
    fs = 13; lh = 19; cw = 7.8; x = 18
    rows = [line(x, 58, prompt() + [("t", "tree ~/stack")], fs), line(x, 58+lh, [("c", "~/stack")], fs)]
    y = 58 + 2*lh; nfiles = 0
    for di, (d, ic, files) in enumerate(TREE):
        lastd = di == len(TREE)-1
        rows.append(f'<text x="{x}" y="{y}" font-size="{fs}" class="d">{"└── " if lastd else "├── "}</text>'
                    f'<text x="{x+4*cw}" y="{y}" font-size="{fs}" fill="{C["eye"]}">{esc(ic)}</text>'
                    f'<text x="{x+8.2*cw}" y="{y}" font-size="{fs}" fill="{C["edge"]}" font-weight="700">{esc(d)}</text>')
        y += lh
        for fi, (f, ext, col) in enumerate(files):
            nfiles += 1
            pre = ("    " if lastd else "│   ") + ("└── " if fi == len(files)-1 else "├── ")
            fx = x + len(pre)*cw
            rows.append(f'<text x="{x}" y="{y}" font-size="{fs}" class="d">{pre}</text><text x="{fx}" y="{y}" font-size="{fs}" class="t">{esc(f)}</text>')
            ex = fx + (len(f)+1)*cw
            rows.append(f'<rect x="{ex-2}" y="{y-11}" width="{len(ext)*6.6+7}" height="14" rx="2" fill="none" stroke="{col}"/><text x="{ex+1.5}" y="{y-0.5}" font-size="11" fill="{col}">{ext}</text>')
            if f == "java":
                rows.append(f'<text x="{ex + len(ext)*6.6+14}" y="{y}" font-size="12" class="a blink">← next: minecraft mod [WIP]</text>')
            y += lh
    y += lh*0.5
    rows.append(line(x, y, [("d", f"{len(TREE)} directories, {nfiles} files")], 12))
    h = int(y + 22)
    return svg_doc(HALF, h, window(HALF, h, "~/stack", ''.join(rows))), h

def build_proc(st, h):
    fs = 13; lh = 21; x = 18
    best = st['best']; cur = st['cur']
    n = 6; fill = 0 if best == 0 else max(1 if cur else 0, round(cur/best*n))
    rec = f"{st['best_from']} → {st['best_to'][5:]}" if st['best_from'] else "-"
    rows = [prompt() + [("t", "cat /proc/streak")],
            [("d", "commits.total  "), ("t", f"{st['total']}")],
            [("d", "commits.since  "), ("t", st['since'] or "-")],
            [("d", "streak.current "), ("a", f"{cur}d  "), ("d", "["), ("e", "█"*fill), ("d", "░"*(n-fill) + "]")],
            [("d", "streak.longest "), ("a", f"{best}d  "), ("d", "["), ("e", "█"*n), ("d", "]")],
            [("d", "streak.record  "), ("t", rec)],
            [("d", "status         "), ("a", "● "), ("t", "online "), ("d", "· grinding")],
            [],
            prompt() + [("t", "uptime")],
            [("d", f" up {max(1, (datetime.date.today() - datetime.date.fromisoformat(st['since'])).days // 365) if st['since'] else 1} years, last sync {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC")]]
    body = ''.join(line(x, 58 + i*lh, r, fs) for i, r in enumerate(rows) if r)
    return svg_doc(HALF, h, window(HALF, h, "/proc/streak", body))

# ---- 6. nekomata.exe (cat hunts the real contribution graph) --------------
def cat_sprite(x, y, s):
    """tiny pixel black cat, 3 cells wide, red eyes."""
    px = s/4.0
    pts = ["..#.#.", ".####.", "######", "#r##r#", ".####.", "##..##"]
    out = []
    for r, rowp in enumerate(pts):
        for c, ch in enumerate(rowp):
            if ch == '.': continue
            col = C['eye'] if ch == 'r' else C['text']
            out.append(f'<rect x="{x + c*px*0.9:.1f}" y="{y + r*px*0.9:.1f}" width="{px*0.9+0.2:.1f}" height="{px*0.9+0.2:.1f}" fill="{col}"/>')
    return ''.join(out)

def build_neko(weeks):
    SC = len(weeks); SR = 7; cs = 14.2; x0 = 22; y0 = 122
    cells = {}
    for c, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            r = d.get("weekday", datetime.date.fromisoformat(d["date"]).isoweekday() % 7)
            lv = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 3}.get(d["contributionLevel"], 0)
            cells[(c, r)] = lv
    path = []
    for r in range(SR):
        cols = range(SC) if r % 2 == 0 else range(SC-1, -1, -1)
        for c in cols: path.append((c, r))
    dt = 0.075; total = len(path)*dt + 2.5
    targets = [(c, r) for (c, r) in path if cells.get((c, r), 0) > 0]
    catch_t = {p: (path.index(p))*dt for p in targets}
    out = []
    gcol = {1: "#5a1a18", 2: C['field'], 3: C['eye']}
    for (c, r), lv in cells.items():
        x = x0 + c*cs; y = y0 + r*cs
        if lv == 0:
            out.append(f'<rect x="{x+3:.1f}" y="{y+3:.1f}" width="{cs-6:.1f}" height="{cs-6:.1f}" rx="1.5" fill="#15121c"/>')
            continue
        t = catch_t[(c, r)] / total
        out.append(f'''<rect x="{x+1.5:.1f}" y="{y+1.5:.1f}" width="{cs-3:.1f}" height="{cs-3:.1f}" rx="2" fill="{gcol[lv]}"><animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;{t:.4f}" values="1;0"/></rect>
<text x="{x+cs/2:.1f}" y="{y+cs-3.5:.1f}" font-size="11" text-anchor="middle" fill="{C['faint']}" opacity="0">×<animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;{t:.4f}" values="0;1"/></text>''')
    # cat motion: discrete positions along path
    xs = ';'.join(f'{x0 + c*cs - cs*0.4:.1f}' for c, r in path) + f';{x0-60}'
    ys = ';'.join(f'{y0 + r*cs - 1:.1f}' for c, r in path) + f';{y0}'
    kt = ';'.join(f'{(i*dt)/total:.4f}' for i in range(len(path))) + f';{len(path)*dt/total:.4f}'
    sprite = cat_sprite(0, 0, cs*1.15)
    out.append(f'''<g><animateTransform attributeName="transform" type="translate" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete"
 keyTimes="{kt}" values="{';'.join(f'{a},{b}' for a, b in zip(xs.split(';'), ys.split(';')))}"/>{sprite}</g>''')
    # counter + progress
    n = len(targets); times = sorted(catch_t[p] for p in targets)
    cnt = []
    for k in range(n+1):
        a = 0 if k == 0 else times[k-1]/total
        b = times[k]/total if k < n else len(path)*dt/total
        cnt.append((k, a, b))
    sx = x0; sy = y0 + SR*cs + 30
    ctr = []
    for k, a, b in cnt:
        bar = round(k/max(1, n)*16)
        vals = "0;1;0" if a > 0 else "1;0"
        kts = f"0;{a:.4f};{b:.4f}" if a > 0 else f"0;{b:.4f}"
        ctr.append(f'''<g opacity="{1 if a == 0 else 0}"><animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kts}" values="{vals}"/>
<text x="{sx}" y="{sy}" font-size="12"><tspan class="d">caught </tspan><tspan class="t">{k}</tspan><tspan class="d">/</tspan><tspan class="t">{n}</tspan></text>
<rect x="{sx+110}" y="{sy-10}" width="160" height="10" fill="none" stroke="{C['line']}"/><rect x="{sx+111}" y="{sy-9}" width="{158*k/max(1,n):.1f}" height="8" fill="{C['eye']}"/></g>''')
    # final purged msg
    tend = len(path)*dt/total
    ctr.append(f'''<text x="{sx + 290}" y="{sy}" font-size="12" class="a" opacity="0">[✓] graph cleared. nekomata naps ...<animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;{tend:.4f}" values="0;1"/></text>''')
    logs = [line(22, 58, prompt() + [("t", "./nekomata.exe --hunt contrib.graph --silent-paws")], 13),
            line(22, 80, [("d", f"[*] sniffing contribution graph ... {SC}x{SR} nodes")], 12),
            line(22, 97, [("p", f"[+] {n} mice detected"), ("d", "   [*] nekomata awake. tails: 2")], 12)]
    h = int(sy + 22)
    body = window(W, h, "nekomata.exe — pid 4040", ''.join(logs) +
                  f'<rect x="{x0-8}" y="{y0-8}" width="{SC*cs+16}" height="{SR*cs+16}" fill="#040306" stroke="{C["line"]}" stroke-dasharray="3 3"/>' +
                  ''.join(out) + ''.join(ctr), mon="● HUNTING")
    return svg_doc(W, h, body)

# ---- 7. ssh ---------------------------------------------------------------
def build_ssh():
    fs = 13; lh = 19; x = 22; cw = 7.8
    L = [prompt("guest", "internet") + [("t", "ssh benji@void")],
         [("d", "Warning: Permanently added 'void' to the list of known hosts.")],
         [("d", "Last login: tonight, from Surabaya")],
         [],
         [("d", "  instagram  "), ("p", "@444xbnji")],
         [("d", "  github     "), ("p", "github.com/BenjiJimaa")],
         [("d", "  collab     "), ("t", "backend, automation, Minecraft mods")],
         [("d", "  dm         "), ("a", "open")],
         [],
         prompt() + [("t", "exit")],
         [("d", "logout")],
         [("e", "Connection to void closed by nekomata.")]]
    total = 16.0
    out = []
    t = 1.2  # after typing ssh command
    appear = []
    for i, r in enumerate(L):
        if i == 0: appear.append(0); continue
        if i == 9: t += 0.6
        appear.append(t); t += 0.35 if r else 0.15
    for i, r in enumerate(L):
        if not r: continue
        y = 58 + i*lh
        a = appear[i]/total
        el = line(x, y, r, fs)
        if i == 0:
            out.append(pline(x, y, "guest", "internet"))
            pl = len("guest@internet:~$ ")
            out.append(typing_single(x + pl*cw, y, "ssh benji@void", 0.0, total, cw, fs, "t"))
            continue
        if i == 9:
            out.append(f'<g opacity="0"><animate attributeName="opacity" dur="{total}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;{a:.4f};0.97" values="0;1;0"/>{pline(x, y)}</g>')
            out.append(typing_single(x + len("benji@void:~$ ")*cw, y, "exit", appear[i]+0.2, total, cw, fs, "t"))
            continue
        out.append(f'<g opacity="0"><animate attributeName="opacity" dur="{total}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;{a:.4f};0.97" values="0;1;0"/>{el}</g>')
    y = 58 + (len(L)-1)*lh
    out.append(f'<text x="{x + 39*cw}" y="{y}" font-size="{fs}" class="t blink" opacity="0">█<animate attributeName="opacity" dur="{total}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;{appear[-1]/total:.4f};0.97" values="0;1;0"/></text>')
    h = int(58 + len(L)*lh + 6)
    return svg_doc(W, h, window(W, h, "guest@internet: ssh", ''.join(out)))

def typing_single(x, y, s, start, total, cw, fs, cls):
    n = len(s); keys = [0.0, start/total]; vals = [0, 0]
    for k in range(1, n+1):
        keys.append((start + 0.07*k)/total); vals.append(k*cw + 1)
    keys.append(0.97); vals.append(n*cw+1)
    keys.append(1.0); vals.append(0)
    ks, vs = [], []
    for k_, v_ in zip(keys, vals):
        if ks and k_ <= ks[-1] + 1e-6: vs[-1] = v_; continue
        ks.append(k_); vs.append(v_)
    cid = f"ts{abs(hash((x, y, s))) % 99999}"
    return f'''<clipPath id="{cid}"><rect x="{x}" y="{y-fs}" height="{fs+6}" width="0"><animate attributeName="width" dur="{total}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{';'.join(f'{k:.4f}' for k in ks)}" values="{';'.join(f'{v:.1f}' for v in vs)}"/></rect></clipPath>
<text x="{x}" y="{y}" font-size="{fs}" class="{cls}" clip-path="url(#{cid})">{esc(s)}</text>'''

# ---- 8. blinking eye footer -----------------------------------------------
RAMP = " ..'',;:ccloodxkO0KXNWMM"
def hsh(x, y):
    n = math.sin(x*12.9898 + y*78.233)*43758.5453
    return n - math.floor(n)

def eye_frame(a, lookX, EW=84, EH=18, A=36, B=16):
    cx = (EW-1)/2; cy = (EH-1)/2 + 0.5
    rows = []
    for r in range(EH):
        row = []
        for c in range(EW):
            x = c - cx; y = (r-cy)*2.15; t = abs(x)/A; v = 0; cls = 'n'
            tt = min(1, t)
            lower = B*0.62*(1-tt*tt)**0.85
            upper = lower + (-B*(1-tt*tt)**0.7 - lower)*a
            n = hsh(c, r) - 0.5
            if t < 1:
                if upper < y < lower:
                    d = math.hypot((x-lookX)*0.92, y); Ri, Rp = 14.5, 6.2
                    eu = y-upper; el = lower-y
                    if d < Rp: v = 0.02
                    elif d < Ri:
                        ang = math.atan2(y, x-lookX); rr = (d-Rp)/(Ri-Rp)
                        v = 0.48 + 0.42*rr + 0.14*math.sin(ang*17 + hsh(round(ang*30), 3)*5) + n*0.1
                        if rr > 0.82: v = 0.97
                        cls = 'i'
                    else:
                        v = (0.46-eu*0.16 if eu < 2.6 else 0) + (0.32-el*0.15 if el < 2 else 0) + (0.06 if n > 0.42 else 0)
                    if eu < 0.9: v = max(v, 0.5)
                else:
                    du = upper-y; dl = y-lower
                    if 0 < du < 5.5: v = (0.62-du*0.1)*(1-t*0.55) + n*0.08
                    elif 5.5 <= du < 9: v = (0.2-(du-5.5)*0.05)*(1-t*0.5) + n*0.05
                    elif 0 < dl < 5: v = (0.4-dl*0.08)*(1-t*0.45) + n*0.06
                    elif 5 <= dl < 8: v = 0.08*(1-t)
            elif t < 1.2:
                yy = y-1.5
                if abs(yy) < 3.2: v = (0.28-abs(yy)*0.07)*(1.2-t)/0.2 + n*0.04
            v = max(0, min(1, v))
            row.append((cls if v > 0.02 else 'n', RAMP[round(v*(len(RAMP)-1))]))
        rows.append(row)
    return rows

def build_eye():
    EW, EH = 84, 18; cw = 8.6; lh = 13.6; fs = 13.2
    x0 = (W - EW*cw)/2; y0 = 18
    frames = {"open": eye_frame(1, 0), "left": eye_frame(1, -9), "right": eye_frame(1, 9),
              "half": eye_frame(.35, 0), "closed": eye_frame(.04, 0)}
    # timeline (seconds): look around + blinks
    seq = [("open", 2.4), ("half", .06), ("closed", .08), ("half", .06), ("open", 1.6), ("left", 1.4), ("open", .5),
           ("right", 1.4), ("open", 1.8), ("half", .06), ("closed", .08), ("half", .06), ("open", .25),
           ("half", .06), ("closed", .08), ("half", .06), ("open", 1.2)]
    total = sum(d for _, d in seq)
    groups = []
    for name, rows in frames.items():
        ks = [0.0]; vs = []; t = 0
        for fn, d in seq:
            on = 1 if fn == name else 0
            if not vs: vs.append(on)
            elif on != vs[-1]: ks.append(t/total); vs.append(on)
            t += d
        txt = []
        for r, row in enumerate(rows):
            runs = []
            for cls, ch in row:
                col = '#f4f1f8' if cls == 'i' else '#d0cbdb'
                if runs and runs[-1][0] == col: runs[-1] = (col, runs[-1][1]+ch)
                else: runs.append((col, ch))
            txt.append(line(f"{x0:.1f}", f"{y0 + (r+1)*lh:.1f}", runs, fs, EW, cw))
        init = vs[0]
        groups.append(f'''<g opacity="{init}"><animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{';'.join(f'{k:.4f}' for k in ks)}" values="{';'.join(map(str, vs))}"/>{''.join(txt)}</g>''')
    h = int(y0 + EH*lh + 44)
    cap = (f'<text x="{W/2-12}" y="{h-14}" font-size="11.5" text-anchor="end" class="d" letter-spacing="1">watch -n 1 /dev/eye</text>'
           f'<text x="{W/2+12}" y="{h-14}" font-size="11.5" class="d" letter-spacing="1">EOF · {USER}</text>')
    return svg_doc(W, h, f'<rect width="{W}" height="{h}" rx="8" fill="#050408"/>' + ''.join(groups) + cap)

def main():
    days, weeks, real = fetch_days()
    st = stats(days)
    print("years:", sorted({d[:4] for d in days}), "stats:", st, "real data" if real else "sample data")
    files = {"cat.svg": build_cat(), "header.svg": build_header(), "whoami.svg": build_whoami(),
             "ps.svg": build_ps(), "nekomata.svg": build_neko(weeks), "ssh.svg": build_ssh(), "eye.svg": build_eye()}
    tree, h = build_tree()
    files["tree.svg"] = tree; files["proc.svg"] = build_proc(st, h)
    for name, svg in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f: f.write(svg)
        print("wrote", name, len(svg)//1024, "KB")

if __name__ == "__main__":
    main()
