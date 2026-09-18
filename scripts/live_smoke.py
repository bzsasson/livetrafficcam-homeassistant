"""One round trip against production, outside pytest (the Home Assistant test
plugin blocks sockets). Run: .venv/bin/python scripts/live_smoke.py"""

import asyncio
import sys
from pathlib import Path

from aiohttp import ClientSession

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from custom_components.livetrafficcam.api import LiveTrafficCamApi  # noqa: E402


async def main() -> int:
    async with ClientSession() as session:
        api = LiveTrafficCamApi(session)
        ents = await api.entities("WA")
        assert any(e["slug"] == "snoqualmie-pass" for e in ents), "entities"
        cams = await api.cams("snoqualmie-pass")
        assert cams and any(c["image"] for c in cams), "cams"
        img = await api.image(next(c["image"] for c in cams if c["image"]))
        assert img[:2] == b"\xff\xd8", "image is not a JPEG"
        ev = await api.events("snoqualmie-pass")
        assert ev["feed"] is not None, "feed"
        print(
            f"ok: {len(ents)} WA entities, {len(cams)} Snoqualmie cams, "
            f"{len(img)} byte still, feed {ev['feed']['agency']} fresh={ev['feed']['fresh']}, "
            f"{len(ev['events'])} events"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
