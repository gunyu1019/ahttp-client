import aiohttp

from flask import Flask
from ahttp_client import AsyncSession, Query, Response, request

app = Flask(__name__)


@app.get("/station/<name>")
@AsyncSession.single_session("https://api.yhs.kr", aiohttp.ClientSession)
@request("GET", "/metro/station")
async def station_search_with_query(session: AsyncSession, response: Response, name: Query | str):
    return response.json()


app.run(host="0.0.0.0", port=8080)
