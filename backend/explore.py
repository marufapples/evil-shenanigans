import httpx

QUERY = """query ($user: String) { MediaListCollection(userName: $user, type: MANGA, status: CURRENT) {
  lists { entries { progress media { id title { romaji english } chapters } } } } }"""

resp = httpx.post("https://graphql.anilist.co", json={"query": QUERY, "variables": {"user": "porkhamhennessy"}})
resp.raise_for_status()
for lst in resp.json()["data"]["MediaListCollection"]["lists"]:
    for e in lst["entries"]:
        t = e["media"]["title"]
        print(f'{t["english"] or t["romaji"]}: chapter {e["progress"]}')