"""Camera entities: one per cam with an image, held frames, attributes."""

from unittest.mock import patch

from homeassistant.components.camera import async_get_image
from homeassistant.helpers import entity_registry as er

from custom_components.livetrafficcam.const import BASE_URL

from .conftest import load_fixture
from .test_init import make_entry, mock_api


async def setup(hass, aioclient_mock):
    mock_api(aioclient_mock)
    entry = make_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def first_image_cam():
    return next(c for c in load_fixture("cams_snoqualmie_pass.json")["cams"] if c["image"])


def camera_entity_id(hass, cam):
    registry = er.async_get(hass)
    return registry.async_get_entity_id("camera", "livetrafficcam", f"livetrafficcam_{cam['id']}")


async def test_one_camera_per_cam_with_image(hass, aioclient_mock):
    await setup(hass, aioclient_mock)
    cams = load_fixture("cams_snoqualmie_pass.json")["cams"]
    with_image = [c for c in cams if c["image"]]
    registry = er.async_get(hass)
    ids = {e.unique_id for e in registry.entities.values() if e.domain == "camera"}
    assert ids == {f"livetrafficcam_{c['id']}" for c in with_image}


async def test_image_fetch_and_hold(hass, aioclient_mock):
    await setup(hass, aioclient_mock)
    cam = first_image_cam()
    aioclient_mock.get(f"{BASE_URL}{cam['image']}", content=b"frame1")
    entity_id = camera_entity_id(hass, cam)
    with patch("custom_components.livetrafficcam.camera.time.monotonic", return_value=1000.0):
        assert (await async_get_image(hass, entity_id)).content == b"frame1"
        calls_before = aioclient_mock.call_count
        assert (await async_get_image(hass, entity_id)).content == b"frame1"
        assert aioclient_mock.call_count == calls_before
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE_URL}{cam['image']}", content=b"frame2")
    with patch("custom_components.livetrafficcam.camera.time.monotonic", return_value=1061.0):
        assert (await async_get_image(hass, entity_id)).content == b"frame2"


async def test_image_failure_keeps_last_frame(hass, aioclient_mock):
    await setup(hass, aioclient_mock)
    cam = first_image_cam()
    aioclient_mock.get(f"{BASE_URL}{cam['image']}", content=b"frame1")
    entity_id = camera_entity_id(hass, cam)
    with patch("custom_components.livetrafficcam.camera.time.monotonic", return_value=1000.0):
        assert (await async_get_image(hass, entity_id)).content == b"frame1"
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE_URL}{cam['image']}", status=502)
    with patch("custom_components.livetrafficcam.camera.time.monotonic", return_value=1061.0):
        assert (await async_get_image(hass, entity_id)).content == b"frame1"


async def test_attributes(hass, aioclient_mock):
    await setup(hass, aioclient_mock)
    cam = first_image_cam()
    state = hass.states.get(camera_entity_id(hass, cam))
    assert state.attributes["live_status"] == cam["live_status"]
    assert state.attributes["route"] == cam["route"]
    assert state.attributes["official_url"] == cam["official_url"]
    assert state.attributes["attribution"] == cam["attribution"]
