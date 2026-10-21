"""Live Traffic Cam: pass, highway, metro and city cameras from livetrafficcam.com."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LiveTrafficCamApi
from .const import CITY_KIND, CONF_KIND, PLATFORMS
from .coordinator import (
    CamsCoordinator,
    EventsCoordinator,
    LiveTrafficCamConfigEntry,
    RuntimeData,
)


async def async_setup_entry(hass: HomeAssistant, entry: LiveTrafficCamConfigEntry) -> bool:
    """Set up one pass, bridge, tunnel, airport, highway, metro area or city."""
    api = LiveTrafficCamApi(async_get_clientsession(hass))
    cams = CamsCoordinator(hass, entry, api)
    # Cities have no event feed on the site, so no events coordinator and no
    # disruption sensors for them (2026-10-21).
    events = None if entry.data.get(CONF_KIND) == CITY_KIND else EventsCoordinator(hass, entry, api)
    # Every first refresh must succeed; a failure raises ConfigEntryNotReady
    # and Home Assistant retries with backoff.
    await cams.async_config_entry_first_refresh()
    if events is not None:
        await events.async_config_entry_first_refresh()
    entry.runtime_data = RuntimeData(api=api, cams=cams, events=events)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LiveTrafficCamConfigEntry) -> bool:
    """Unload one entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
