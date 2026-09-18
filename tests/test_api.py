"""The API client against a mocked livetrafficcam.com."""

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.livetrafficcam.api import ApiError, LiveTrafficCamApi
from custom_components.livetrafficcam.const import BASE_URL, USER_AGENT

from .conftest import load_fixture


async def test_entities_returns_list_and_sends_user_agent(hass, aioclient_mock):
    aioclient_mock.get(
        f"{BASE_URL}/api/entities.json?state=WA", json=load_fixture("entities_wa.json")
    )
    api = LiveTrafficCamApi(async_get_clientsession(hass))
    out = await api.entities("WA")
    assert out and out[0]["slug"]
    headers = aioclient_mock.mock_calls[0][3]
    assert headers["User-Agent"] == USER_AGENT


async def test_cams_and_events(hass, aioclient_mock):
    aioclient_mock.get(
        f"{BASE_URL}/api/cams.json?entity=snoqualmie-pass",
        json=load_fixture("cams_snoqualmie_pass.json"),
    )
    aioclient_mock.get(
        f"{BASE_URL}/api/events.json?entity=snoqualmie-pass",
        json=load_fixture("events_snoqualmie_pass.json"),
    )
    api = LiveTrafficCamApi(async_get_clientsession(hass))
    cams = await api.cams("snoqualmie-pass")
    assert all("id" in c and "image" in c for c in cams)
    ev = await api.events("snoqualmie-pass")
    assert ev["feed"]["agency"] and isinstance(ev["events"], list)


async def test_image_bytes(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/img/14389.jpg", content=b"\xff\xd8jpeg")
    api = LiveTrafficCamApi(async_get_clientsession(hass))
    assert await api.image("/img/14389.jpg") == b"\xff\xd8jpeg"


@pytest.mark.parametrize("status", [404, 500, 503])
async def test_non_200_raises(hass, aioclient_mock, status):
    aioclient_mock.get(f"{BASE_URL}/api/cams.json?entity=x", status=status)
    api = LiveTrafficCamApi(async_get_clientsession(hass))
    with pytest.raises(ApiError):
        await api.cams("x")


@pytest.mark.parametrize(
    "path", ["https://evil.example/x.jpg", "/api/cams.json", "/img/../x", "//evil/x"]
)
async def test_image_refuses_non_proxy_paths(hass, aioclient_mock, path):
    api = LiveTrafficCamApi(async_get_clientsession(hass))
    with pytest.raises(ApiError):
        await api.image(path)
    assert aioclient_mock.call_count == 0


async def test_image_refuses_oversized_body(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/img/1.jpg", content=b"x" * (4 * 1024 * 1024 + 1))
    api = LiveTrafficCamApi(async_get_clientsession(hass))
    with pytest.raises(ApiError):
        await api.image("/img/1.jpg")
