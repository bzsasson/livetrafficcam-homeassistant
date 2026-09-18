"""Polling coordinators: cams every five minutes, events every ten."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiError, LiveTrafficCamApi
from .const import (
    CAMS_INTERVAL,
    CONF_CAM_IDS,
    CONF_KIND,
    CONF_NAME,
    CONF_PAGE,
    CONF_SLUG,
    CONF_STATE,
    DOMAIN,
    EVENTS_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

KIND_MODEL = {
    "pass": "Mountain pass",
    "bridge": "Bridge",
    "tunnel": "Tunnel",
    "airport": "Airport",
    "corridor": "Highway",
}


class CamsCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """The entry's selected cameras, keyed by id."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: LiveTrafficCamApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} cams {entry.data[CONF_SLUG]}",
            update_interval=CAMS_INTERVAL,
        )
        self.api = api
        self.slug: str = entry.data[CONF_SLUG]
        self._wanted: set[int] = set(entry.data[CONF_CAM_IDS])

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        try:
            cams = await self.api.cams(self.slug)
        except ApiError as err:
            raise UpdateFailed(str(err)) from err
        return {c["id"]: c for c in cams if c.get("id") in self._wanted}


class EventsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """The entry's reported disruptions and feed status."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: LiveTrafficCamApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} events {entry.data[CONF_SLUG]}",
            update_interval=EVENTS_INTERVAL,
        )
        self.api = api
        self.slug: str = entry.data[CONF_SLUG]

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.events(self.slug)
        except ApiError as err:
            raise UpdateFailed(str(err)) from err


@dataclass
class RuntimeData:
    """What a loaded config entry carries."""

    api: LiveTrafficCamApi
    cams: CamsCoordinator
    events: EventsCoordinator


type LiveTrafficCamConfigEntry = ConfigEntry[RuntimeData]


def device_info_for(entry: ConfigEntry, attribution: str | None) -> DeviceInfo:
    """One device per config entry; its configuration link is the pass page."""
    manufacturer = (attribution or "").removeprefix("Camera: ").strip() or "livetrafficcam.com"
    return DeviceInfo(
        identifiers={(DOMAIN, entry.data[CONF_SLUG])},
        name=f"{entry.data[CONF_NAME]} ({entry.data[CONF_STATE]})",
        manufacturer=manufacturer,
        model=KIND_MODEL.get(entry.data[CONF_KIND], "Cameras"),
        configuration_url=entry.data[CONF_PAGE],
    )
