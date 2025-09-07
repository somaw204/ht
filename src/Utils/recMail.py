import re
import asyncio
import httpx

async def get_key():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://smailpro.com/app/key",
                json={
                    "domain": "gmail.com",
                    "username": "random",
                    "server": "server-1",
                    "type": "alias",
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3",
                    "Content-Type": "application/json",
                    "x-g-token": "",
                    "X-XSRF-TOKEN": "",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin",
                },
            )
            return response.json().get("items")
    except Exception as error:
        print("Errore:", error)

async def get_email():
    try:
        key = await get_key()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.sonjj.com/email/gm/get",
                params={
                    "key": key,
                    "domain": "gmail.com",
                    "username": "random",
                    "server": "server-1",
                    "type": "alias",
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3",
                    "x-rapidapi-ua": "RapidAPI-Playground",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "cross-site",
                },
            )
            return response.json().get("items")
    except Exception as error:
        print("Errore:", error)

async def get_mid(email):
    await delay(10000)
    try:
        key = await get_key()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.sonjj.com/email/gm/check",
                params={
                    "key": key,
                    "rapidapi-key": "f871a22852mshc3ccc49e34af1e8p126682jsn734696f1f081",
                    "email": email["email"],
                    "timestamp": email["timestamp"],
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3",
                    "x-rapidapi-ua": "RapidAPI-Playground",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "cross-site",
                },
            )
            return response.json().get("items", [{}])[0].get("mid")
    except Exception:
        return await get_mid(email)

async def get_message(email):
    try:
        mid = await get_mid(email)
        key = await get_key()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.sonjj.com/email/gm/read",
                params={
                    "key": key,
                    "rapidapi-key": "f871a22852mshc3ccc49e34af1e8p126682jsn734696f1f081",
                    "email": email["email"],
                    "message_id": mid,
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3",
                    "x-rapidapi-ua": "RapidAPI-Playground",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "cross-site",
                },
            )
            body = response.json().get("items", {}).get("body", "")
            match = re.search(r">\s*(\d{6})\s*<\/span>", body)
            return match.group(1) if match else None
    except Exception as error:
        print("Errore:", error)

async def delay(time: int):
    await asyncio.sleep(time / 1000)

__all__ = ["get_email", "get_message"]
