import re
import sys
import asyncio
import httpx

IMAGE_PATTERN = r'og:image[^>]*content="(https://[^"]+/images/anime/[^"]+)"'
URL_ANIME = 'https://myanimelist.net/anime/'
URL_ANIMELIST = 'https://myanimelist.net/animelist/{}/load.json?offset={}&status=7'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


async def fetch_anime_ids(client, username):
    ids = []
    offset = 0
    while True:
        r = await client.get(URL_ANIMELIST.format(username, offset))
        data = r.json()
        if not data:
            break
        ids.extend(str(entry['anime_id']) for entry in data)
        if len(data) < 300:
            break
        offset += 300
    return ids


async def fetch_cover(client, anime_ref):
    for attempt in range(5):
        try:
            r = await client.get(URL_ANIME + anime_ref)
            r.raise_for_status()
            matches = re.findall(IMAGE_PATTERN, r.text)
            if matches:
                return (anime_ref, matches[0])
            return None
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            status = e.response.status_code if isinstance(e, httpx.HTTPStatusError) else 0
            wait = 2 ** attempt
            print(f"  [{anime_ref}] error {status}, retry in {wait}s")
            await asyncio.sleep(wait)
    return None


async def main(username, output_file):
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        refs = await fetch_anime_ids(client, username)
        print(f"Found {len(refs)} anime for {username}")

        results = await asyncio.gather(*[fetch_cover(client, ref) for ref in refs])

    with open(output_file, 'w+') as f:
        for result in results:
            if result:
                ref, url = result
                f.write(f'#more{ref}{{background-image: url("{url}");}}\n')

    written = sum(1 for r in results if r)
    print(f"Written {written} cover rules to {output_file}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: generate_covers.py <username> [output_file]")
        sys.exit(1)

    asyncio.run(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'covers.css'))
