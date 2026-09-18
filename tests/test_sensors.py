"""Sensors and binary sensors."""

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.helpers import entity_registry as er

from custom_components.livetrafficcam.const import BASE_URL

from .conftest import load_fixture
from .test_init import make_entry


async def setup(hass, aioclient_mock, events=None):
    aioclient_mock.get(
        f"{BASE_URL}/api/cams.json?entity=snoqualmie-pass",
        json=load_fixture("cams_snoqualmie_pass.json"),
    )
    aioclient_mock.get(
        f"{BASE_URL}/api/events.json?entity=snoqualmie-pass",
        json=events if events is not None else load_fixture("events_snoqualmie_pass.json"),
    )
    entry = make_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def eid(hass, domain, unique_id):
    return er.async_get(hass).async_get_entity_id(domain, "livetrafficcam", unique_id)


async def test_link_out_cam_is_a_sensor_not_a_camera(hass, aioclient_mock):
    await setup(hass, aioclient_mock)
    cams = load_fixture("cams_snoqualmie_pass.json")["cams"]
    link = next(c for c in cams if not c["image"])
    assert eid(hass, "camera", f"livetrafficcam_{link['id']}") is None
    state = hass.states.get(eid(hass, "sensor", f"livetrafficcam_{link['id']}_link"))
    assert state.state == link["live_status"]
    assert state.attributes["official_url"] == link["official_url"]


async def test_live_count_and_verified_live(hass, aioclient_mock):
    await setup(hass, aioclient_mock)
    cams = load_fixture("cams_snoqualmie_pass.json")["cams"]
    live = [c for c in cams if c["live_status"] == "live"]
    assert len(live) < len(cams)  # the fixture holds one stale cam on purpose
    count = hass.states.get(eid(hass, "sensor", "livetrafficcam_snoqualmie-pass_live_count"))
    assert int(count.state) == len(live)
    assert count.attributes["total"] == len(cams)
    for c in cams:
        s = hass.states.get(eid(hass, "binary_sensor", f"livetrafficcam_{c['id']}_live"))
        assert s.state == (STATE_ON if c["live_status"] == "live" else STATE_OFF)


async def test_disruption_sensors_from_fixture(hass, aioclient_mock):
    await setup(hass, aioclient_mock)
    d = hass.states.get(eid(hass, "binary_sensor", "livetrafficcam_snoqualmie-pass_disruption"))
    c = hass.states.get(eid(hass, "binary_sensor", "livetrafficcam_snoqualmie-pass_closure"))
    assert d.state == STATE_ON
    assert d.attributes["count"] == 2
    assert len(d.attributes["headlines"]) == 2
    assert d.attributes["agency"] == "WSDOT"
    assert c.state == STATE_ON
    assert c.attributes["headline"]


async def test_no_events_is_off_when_feed_fresh(hass, aioclient_mock):
    ev = load_fixture("events_snoqualmie_pass.json")
    ev["events"] = []
    await setup(hass, aioclient_mock, events=ev)
    d = eid(hass, "binary_sensor", "livetrafficcam_snoqualmie-pass_disruption")
    c = eid(hass, "binary_sensor", "livetrafficcam_snoqualmie-pass_closure")
    assert hass.states.get(d).state == STATE_OFF
    assert hass.states.get(c).state == STATE_OFF


async def test_stale_or_missing_feed_is_unavailable(hass, aioclient_mock):
    ev = load_fixture("events_snoqualmie_pass.json")
    ev["events"] = []
    ev["feed"]["fresh"] = False
    await setup(hass, aioclient_mock, events=ev)
    d = eid(hass, "binary_sensor", "livetrafficcam_snoqualmie-pass_disruption")
    c = eid(hass, "binary_sensor", "livetrafficcam_snoqualmie-pass_closure")
    assert hass.states.get(d).state == STATE_UNAVAILABLE
    assert hass.states.get(c).state == STATE_UNAVAILABLE


async def test_null_feed_is_unavailable(hass, aioclient_mock):
    ev = {"entity": "snoqualmie-pass", "feed": None, "events": []}
    await setup(hass, aioclient_mock, events=ev)
    d = eid(hass, "binary_sensor", "livetrafficcam_snoqualmie-pass_disruption")
    assert hass.states.get(d).state == STATE_UNAVAILABLE
