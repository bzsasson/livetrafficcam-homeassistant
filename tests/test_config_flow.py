"""Config flow: state, entity, cameras."""

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.livetrafficcam.const import BASE_URL, CONF_CAM_IDS, CONF_SLUG, DOMAIN

from .conftest import load_fixture


def mock_lists(aioclient_mock):
    aioclient_mock.get(
        f"{BASE_URL}/api/entities.json?state=WA", json=load_fixture("entities_wa.json")
    )
    aioclient_mock.get(
        f"{BASE_URL}/api/cams.json?entity=snoqualmie-pass",
        json=load_fixture("cams_snoqualmie_pass.json"),
    )


async def start(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_full_flow_pass(hass, aioclient_mock):
    mock_lists(aioclient_mock)
    result = await start(hass)
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"state": "WA"})
    assert result["step_id"] == "entity"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity": "snoqualmie-pass"}
    )
    assert result["step_id"] == "cameras"
    cams = load_fixture("cams_snoqualmie_pass.json")["cams"]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"cameras": [str(c["id"]) for c in cams]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Snoqualmie Pass (WA)"
    assert result["data"][CONF_SLUG] == "snoqualmie-pass"
    assert result["data"][CONF_CAM_IDS] == [c["id"] for c in cams]


async def test_duplicate_aborts(hass, aioclient_mock):
    mock_lists(aioclient_mock)
    MockConfigEntry(domain=DOMAIN, unique_id="snoqualmie-pass", data={}).add_to_hass(hass)
    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"state": "WA"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity": "snoqualmie-pass"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_empty_state_aborts(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/api/entities.json?state=WY", json={"entities": []})
    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"state": "WY"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_entities"


async def test_connection_error_shows_form_again(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/api/entities.json?state=WA", status=503)
    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"state": "WA"})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_unknown_entity_is_rejected(hass, aioclient_mock):
    # The selector schema refuses a value the flow did not offer before the
    # step handler runs; the handler's own check is the second layer.
    mock_lists(aioclient_mock)
    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"state": "WA"})
    with pytest.raises(InvalidData):
        await hass.config_entries.flow.async_configure(
            result["flow_id"], {"entity": "not-offered"}
        )


async def test_highway_requires_selection_and_caps(hass, aioclient_mock):
    entities = load_fixture("entities_wa.json")
    highway = next(e for e in entities["entities"] if e["kind"] == "corridor")
    aioclient_mock.get(f"{BASE_URL}/api/entities.json?state=WA", json=entities)
    big = {"cams": [{"id": i, "name": f"Cam {i}", "image": f"/img/{i}.jpg"} for i in range(1, 41)]}
    aioclient_mock.get(f"{BASE_URL}/api/cams.json?entity={highway['slug']}", json=big)
    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"state": "WA"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity": highway["slug"]}
    )
    assert result["step_id"] == "cameras"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"cameras": []})
    assert result["errors"] == {"cameras": "select_at_least_one"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"cameras": [str(i) for i in range(1, 30)]}
    )
    assert result["errors"] == {"cameras": "too_many"}
    with pytest.raises(InvalidData):
        await hass.config_entries.flow.async_configure(
            result["flow_id"], {"cameras": ["1", "999"]}
        )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"cameras": ["1", "2", "3"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_CAM_IDS] == [1, 2, 3]
