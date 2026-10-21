#!/usr/bin/env python3
"""Build every image of the BenjiJimaa profile README into OUT_DIR.

Live sections (redrawn daily with real data from the GitHub GraphQL API):
  neofetch.svg  - <B> logo + [ benji@void ] card, uptime and GitHub stats
  netwatch.svg  - the contribution year as an intercept monitor
Static sections (copied as-is from assets/):
  hello.svg, whoami.svg, missions.svg, logout.svg

Runs in GitHub Actions with GITHUB_TOKEN. Without a token (local test) it falls
back to sample numbers so the layout can still be checked.
"""
import os, sys, json, shutil, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import card, activity

USER = os.environ.get("PROFILE_USER", "BenjiJimaa")
OUT = os.environ.get("OUT_DIR", "dist")
TOKEN = os.environ.get("GITHUB_TOKEN")
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).date()   # WIB
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def gql(query, variables=None):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.load(r)
    if "errors" in res:
        raise RuntimeError(res["errors"])
    return res["data"]


def fetch():
    u = gql("""query($u:String!){user(login:$u){
      id followers{totalCount}
      repositories(ownerAffiliations:OWNER, first:100){totalCount nodes{name isFork stargazerCount defaultBranchRef{name}}}
      repositoriesContributedTo(first:1, includeUserRepositories:false,
        contributionTypes:[COMMIT, PULL_REQUEST, REPOSITORY, PULL_REQUEST_REVIEW]){totalCount}
      contributionsCollection{contributionYears contributionCalendar{weeks{contributionDays{date contributionCount contributionLevel}}}}
    }}""", {"u": USER})["user"]

    # commits: every year since the account started
    commits = 0
    for y in u["contributionsCollection"]["contributionYears"]:
        cc = gql("""query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){
          contributionsCollection(from:$f,to:$t){totalCommitContributions}}}""",
                 {"u": USER, "f": f"{y}-01-01T00:00:00Z", "t": f"{y}-12-31T23:59:59Z"})
        commits += cc["user"]["contributionsCollection"]["totalCommitContributions"]

    # lines of code: additions / deletions of my commits on the default branch of my own repos
    add = dele = 0
    for repo in u["repositories"]["nodes"]:
        if repo["isFork"] or not repo["defaultBranchRef"]:
            continue
        cursor = None
        try:
            while True:
                h = gql("""query($o:String!,$n:String!,$id:ID!,$c:String){repository(owner:$o,name:$n){defaultBranchRef{target{
                  ... on Commit{history(first:100, after:$c, author:{id:$id}){pageInfo{hasNextPage endCursor} nodes{additions deletions}}}}}}}""",
                        {"o": USER, "n": repo["name"], "id": u["id"], "c": cursor})
                hist = h["repository"]["defaultBranchRef"]["target"]["history"]
                for n in hist["nodes"]:
                    add += n["additions"]; dele += n["deletions"]
                if not hist["pageInfo"]["hasNextPage"]:
                    break
                cursor = hist["pageInfo"]["endCursor"]
        except Exception as e:                      # one unreadable repo shouldn't kill the whole card
            print("skip LOC for", repo["name"], "->", e)

    stats = dict(repos=u["repositories"]["totalCount"],
                 contrib=u["repositoriesContributedTo"]["totalCount"],
                 stars=sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
                 commits=commits, followers=u["followers"]["totalCount"],
                 loc=add - dele, add=add, **{"del": dele})
    days = [(d["date"], d["contributionCount"], LEVEL.get(d["contributionLevel"], 0))
            for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    days = [d for d in days if d[0] <= TODAY.isoformat()]
    return stats, days


def sample():
    stats = dict(repos=19, contrib=4, stars=0, commits=231, followers=2, loc=18452, add=21390, **{"del": 2938})
    start = TODAY - datetime.timedelta(days=364)
    hits = {"2025-11-20": (3, 2), "2026-06-19": (1, 1), "2026-10-17": (6, 3), "2026-10-18": (3, 2)}
    days = []
    for k in range(365):
        d = (start + datetime.timedelta(days=k)).isoformat()
        n, lv = hits.get(d, (0, 0))
        days.append((d, n, lv))
    return stats, days


def main():
    os.makedirs(OUT, exist_ok=True)
    if TOKEN:
        stats, days = fetch()
    elif os.environ.get("CI"):
        raise SystemExit("GITHUB_TOKEN missing: refusing to publish sample data")
    else:
        print("no GITHUB_TOKEN: using sample data")
        stats, days = sample()
    print("stats", stats, "| active days", sum(1 for d in days if d[2]))

    with open(os.path.join(OUT, "neofetch.svg"), "w", encoding="utf-8") as f:
        f.write(card.render(stats, TODAY))
    with open(os.path.join(OUT, "netwatch.svg"), "w", encoding="utf-8") as f:
        f.write(activity.build(days, today=TODAY))
    for name in ("hello.svg", "whoami.svg", "missions.svg", "logout.svg"):
        shutil.copy(os.path.join(ROOT, "assets", name), os.path.join(OUT, name))
    print("built:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
