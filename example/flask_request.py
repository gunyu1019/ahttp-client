import asyncio

import aiohttp

from flask import Flask
from async_client_decorator import request, Session, Query

app = Flask(__name__)
loop = asyncio.get_event_loop()


@app.get("/station/<name>")
@Session.single_session("https://api.yhs.kr")
@request("GET", "/metro/station")
async def station_search_with_query(session: Session, response: aiohttp.ClientResponse, name: Query | str):
    return await response.json()


app.run(host="0.0.0.0", port=8080)
