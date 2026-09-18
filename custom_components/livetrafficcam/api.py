"""Thin async client for livetrafficcam.com's public API."""

from __future__ import annotations

from typing import Any

import aiohttp

from .const import BASE_URL, MAX_IMAGE_BYTES, USER_AGENT

TIMEOUT = aiohttp.ClientTimeout(total=20)


class ApiError(Exception):
    """A request to livetrafficcam.com failed or returned a non-200 status."""


class LiveTrafficCamApi:
    """The four GET endpoints the integration uses. No auth, no keys."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str = BASE_URL) -> None:
        self._session = session
        self._base = base_url.rstrip("/")
        self._headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    async def _get_json(self, path: str, params: dict[str, str] | None = None) -> Any:
        try:
            async with self._session.get(
                f"{self._base}{path}", params=params, headers=self._headers, timeout=TIMEOUT
            ) as resp:
                if resp.status != 200:
                    raise ApiError(f"{path} returned {resp.status}")
                return await resp.json(content_type=None)
        except (TimeoutError, aiohttp.ClientError) as err:
            raise ApiError(f"{path}: {err}") from err

    async def entities(self, state: str) -> list[dict[str, Any]]:
        body = await self._get_json("/api/entities.json", {"state": state})
        return list(body.get("entities", []))

    async def cams(self, slug: str) -> list[dict[str, Any]]:
        body = await self._get_json("/api/cams.json", {"entity": slug})
        return list(body.get("cams", []))

    async def events(self, slug: str) -> dict[str, Any]:
        return dict(await self._get_json("/api/events.json", {"entity": slug}))

    async def image(self, path: str) -> bytes:
        """Fetch a still through the site's image proxy.

        `path` is the API's site-relative image and must start with /img/:
        the integration never fetches an arbitrary URL, even one the API
        handed it. Bodies over MAX_IMAGE_BYTES are refused.
        """
        if not path.startswith("/img/") or "//" in path or ".." in path:
            raise ApiError(f"refusing image path {path!r}")
        try:
            async with self._session.get(
                f"{self._base}{path}", headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
            ) as resp:
                if resp.status != 200:
                    raise ApiError(f"{path} returned {resp.status}")
                declared = resp.headers.get("Content-Length")
                if declared and declared.isdigit() and int(declared) > MAX_IMAGE_BYTES:
                    raise ApiError(f"{path} is {declared} bytes, over the cap")
                data = await resp.read()
                if len(data) > MAX_IMAGE_BYTES:
                    raise ApiError(f"{path} exceeded {MAX_IMAGE_BYTES} bytes")
                return data
        except (TimeoutError, aiohttp.ClientError) as err:
            raise ApiError(f"{path}: {err}") from err
