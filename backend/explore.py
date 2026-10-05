import httpx
from datetime import datetime

QUERY = """query ($user: String) { MediaListCollection(userName: $user, type: MANGA, status: CURRENT) {
  lists { entries { progress updatedAt media { id title { romaji english } chapters status coverImage { large } } } } } }"""

resp = httpx.post("https://graphql.anilist.co", json={"query": QUERY, "variables": {"user": "porkhamhennessy"}})
resp.raise_for_status()
print("Remaining requests:", resp.headers.get("X-RateLimit-Remaining"), "/", resp.headers.get("X-RateLimit-Limit"))

for lst in resp.json()["data"]["MediaListCollection"]["lists"]:
    for e in lst["entries"]:
        m, t = e["media"], e["media"]["title"]
        updated = datetime.fromtimestamp(e["updatedAt"]).strftime("%b %d, %Y")
        print(f'{t["english"] or t["romaji"]} | ch {e["progress"]} | {m["status"]} | total: {m["chapters"]} | updated {updated}')