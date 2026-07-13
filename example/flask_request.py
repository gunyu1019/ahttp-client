import aiohttp

from flask import Flask
from ahttp_client import request, BaseSession, Query

app = Flask(__name__)


@app.get("/station/<name>")
@BaseSession.single_session("https://api.yhs.kr")
@request("GET", "/metro/station")
async def station_search_with_query(session: BaseSession, response: aiohttp.ClientResponse, name: Query | str):
    return await response.json()


app.run(host="0.0.0.0", port=8080)
