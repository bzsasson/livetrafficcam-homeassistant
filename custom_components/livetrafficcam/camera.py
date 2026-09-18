"""One camera entity per selected cam that has a proxied still."""

from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ApiError
from .const import DOMAIN, IMAGE_HOLD_SECONDS
from .coordinator import CamsCoordinator, LiveTrafficCamConfigEntry, device_info_for

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LiveTrafficCamConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add a camera for every selected cam the site may show inline."""
    rd = entry.runtime_data
    async_add_entities(
        LiveTrafficCamCamera(rd.cams, entry, cam_id)
        for cam_id, cam in rd.cams.data.items()
        if cam.get("image")
    )


class LiveTrafficCamCamera(CoordinatorEntity[CamsCoordinator], Camera):
    """A still image through the site's proxy, held in memory for a minute."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: CamsCoordinator, entry: LiveTrafficCamConfigEntry, cam_id: int
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._cam_id = cam_id
        self._attr_unique_id = f"{DOMAIN}_{cam_id}"
        self._last_bytes: bytes | None = None
        self._last_fetch: float = 0.0
        cam = self._cam
        self._attr_name = cam["name"]
        self._attr_attribution = cam.get("attribution")
        self._attr_device_info = device_info_for(entry, cam.get("attribution"))

    @property
    def _cam(self) -> dict[str, Any]:
        return self.coordinator.data[self._cam_id]

    @property
    def available(self) -> bool:
        return super().available and self._cam_id in self.coordinator.data

    @property
    def is_on(self) -> bool:
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        cam = self._cam
        return {
            "live_status": cam.get("live_status"),
            "last_live_at": cam.get("last_live_at"),
            "route": cam.get("route"),
            "official_url": cam.get("official_url"),
            "attribution": cam.get("attribution"),
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        # Hold the last frame for IMAGE_HOLD_SECONDS: the camera card asks for
        # a fresh still every few seconds while on screen, and the proxy's own
        # edge copy lives five minutes. Nothing is written to disk.
        now = time.monotonic()
        if self._last_bytes is not None and now - self._last_fetch < IMAGE_HOLD_SECONDS:
            return self._last_bytes
        path = self._cam.get("image")
        if not path:
            return self._last_bytes
        try:
            self._last_bytes = await self.coordinator.api.image(path)
            self._last_fetch = now
        except ApiError as err:
            _LOGGER.debug("image fetch failed for cam %s: %s", self._cam_id, err)
        return self._last_bytes
