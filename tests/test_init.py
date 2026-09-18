"""Entry setup, unload and retry."""

from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.livetrafficcam.const import (
    BASE_URL,
    CONF_CAM_IDS,
    CONF_KIND,
    CONF_NAME,
    CONF_PAGE,
    CONF_ROUTE,
    CONF_SLUG,
    CONF_STATE,
    DOMAIN,
)

from .conftest import load_fixture


def make_entry(cam_ids=None):
    """A Snoqualmie Pass entry over the fixture cams."""
    cams = load_fixture("cams_snoqualmie_pass.json")["cams"]
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="snoqualmie-pass",
        title="Snoqualmie Pass (WA)",
        data={
            CONF_STATE: "WA",
            CONF_SLUG: "snoqualmie-pass",
            CONF_NAME: "Snoqualmie Pass",
            CONF_KIND: "pass",
            CONF_ROUTE: "I-90",
            CONF_PAGE: "https://livetrafficcam.com/traffic-cameras/washington/snoqualmie-pass/",
            CONF_CAM_IDS: cam_ids if cam_ids is not None else [c["id"] for c in cams],
        },
    )


def mock_api(aioclient_mock):
    """Mock both polled endpoints with the fixtures."""
    aioclient_mock.get(
        f"{BASE_URL}/api/cams.json?entity=snoqualmie-pass",
        json=load_fixture("cams_snoqualmie_pass.json"),
    )
    aioclient_mock.get(
        f"{BASE_URL}/api/events.json?entity=snoqualmie-pass",
        json=load_fixture("events_snoqualmie_pass.json"),
    )


async def test_setup_and_unload(hass, aioclient_mock):
    mock_api(aioclient_mock)
    entry = make_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    rd = entry.runtime_data
    assert set(rd.cams.data) == set(entry.data[CONF_CAM_IDS])
    assert rd.events.data["feed"]["agency"]
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_cam_ids_filter(hass, aioclient_mock):
    mock_api(aioclient_mock)
    first = load_fixture("cams_snoqualmie_pass.json")["cams"][0]["id"]
    entry = make_entry(cam_ids=[first])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert list(entry.runtime_data.cams.data) == [first]


async def test_setup_retries_when_api_down(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/api/cams.json?entity=snoqualmie-pass", status=503)
    aioclient_mock.get(f"{BASE_URL}/api/events.json?entity=snoqualmie-pass", status=503)
    entry = make_entry()
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
