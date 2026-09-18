"""Config flow: state, then entity, then cameras. No keys, no free-text URLs."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import ApiError, LiveTrafficCamApi
from .const import (
    CONF_CAM_IDS,
    CONF_KIND,
    CONF_NAME,
    CONF_PAGE,
    CONF_ROUTE,
    CONF_SLUG,
    CONF_STATE,
    DOMAIN,
    FEATURE_KINDS,
    HIGHWAY_MAX_CAMS,
    US_STATES,
)


def _entity_label(e: dict[str, Any]) -> str:
    if e["kind"] == "corridor" and e.get("route"):
        base = f"{e['name']} ({e['route']})"
    else:
        base = e["name"]
    count = e.get("cam_count", 0)
    return f"{base}, {count} camera{'' if count == 1 else 's'}"


class LiveTrafficCamConfigFlow(ConfigFlow, domain=DOMAIN):
    """Three steps, every choice from a list the flow fetched itself."""

    VERSION = 1

    def __init__(self) -> None:
        self._state: str | None = None
        self._entities: dict[str, dict[str, Any]] = {}
        self._entity: dict[str, Any] | None = None
        self._cams: list[dict[str, Any]] = []

    @property
    def _api(self) -> LiveTrafficCamApi:
        return LiveTrafficCamApi(async_get_clientsession(self.hass))

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._state = user_input[CONF_STATE]
            try:
                rows = await self._api.entities(self._state)
            except ApiError:
                errors["base"] = "cannot_connect"
            else:
                if not rows:
                    return self.async_abort(reason="no_entities")
                # Passes, bridges and tunnels first, highways after; API order within each.
                features = [e for e in rows if e.get("kind") in FEATURE_KINDS]
                highways = [e for e in rows if e.get("kind") == "corridor"]
                self._entities = {e["slug"]: e for e in features + highways}
                return await self.async_step_entity()
        options = [SelectOptionDict(value=abbr, label=name) for abbr, name in US_STATES.items()]
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATE): SelectSelector(
                        SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            # Only a slug this flow offered is accepted (data, not trust).
            chosen = self._entities.get(str(user_input.get("entity", "")))
            if chosen is None:
                errors["base"] = "unknown_entity"
            else:
                self._entity = chosen
                await self.async_set_unique_id(chosen["slug"])
                self._abort_if_unique_id_configured()
                try:
                    self._cams = await self._api.cams(chosen["slug"])
                except ApiError:
                    errors["base"] = "cannot_connect"
                else:
                    return await self.async_step_cameras()
        options = [
            SelectOptionDict(value=slug, label=_entity_label(e))
            for slug, e in self._entities.items()
        ]
        return self.async_show_form(
            step_id="entity",
            data_schema=vol.Schema(
                {
                    vol.Required("entity"): SelectSelector(
                        SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_cameras(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._entity is not None
        is_highway = self._entity["kind"] == "corridor"
        errors: dict[str, str] = {}
        if user_input is not None:
            requested = [str(v) for v in user_input.get("cameras", [])]
            offered = {str(c["id"]) for c in self._cams}
            picked = [v for v in requested if v in offered]
            chosen = [int(v) for v in picked]
            if len(picked) != len(requested):
                errors["cameras"] = "unknown_camera"
            elif not chosen:
                errors["cameras"] = "select_at_least_one"
            elif is_highway and len(chosen) > HIGHWAY_MAX_CAMS:
                errors["cameras"] = "too_many"
            else:
                e = self._entity
                state = e.get("state") or self._state
                return self.async_create_entry(
                    title=f"{e['name']} ({state})",
                    data={
                        CONF_STATE: state,
                        CONF_SLUG: e["slug"],
                        CONF_NAME: e["name"],
                        CONF_KIND: e["kind"],
                        CONF_ROUTE: e.get("route"),
                        CONF_PAGE: e["page"],
                        CONF_CAM_IDS: chosen,
                    },
                )
        options = [SelectOptionDict(value=str(c["id"]), label=c["name"]) for c in self._cams]
        default = [] if is_highway else [str(c["id"]) for c in self._cams]
        return self.async_show_form(
            step_id="cameras",
            data_schema=vol.Schema(
                {
                    vol.Required("cameras", default=default): SelectSelector(
                        SelectSelectorConfig(
                            options=options, multiple=True, mode=SelectSelectorMode.LIST
                        )
                    )
                }
            ),
            errors=errors,
            description_placeholders={"max": str(HIGHWAY_MAX_CAMS), "count": str(len(self._cams))},
        )
