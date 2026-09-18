"""Link-out cams as sensors, plus a cameras-live count per entry."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CamsCoordinator, LiveTrafficCamConfigEntry, device_info_for


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LiveTrafficCamConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the live count and one sensor per link-out cam."""
    rd = entry.runtime_data
    entities: list[SensorEntity] = [LiveCountSensor(rd.cams, entry)]
    entities.extend(
        LinkOutSensor(rd.cams, entry, cam_id)
        for cam_id, cam in rd.cams.data.items()
        if not cam.get("image")
    )
    async_add_entities(entities)


class LinkOutSensor(CoordinatorEntity[CamsCoordinator], SensorEntity):
    """A camera whose source only allows linking: no image here, same as the site."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:cctv"

    def __init__(
        self, coordinator: CamsCoordinator, entry: LiveTrafficCamConfigEntry, cam_id: int
    ) -> None:
        super().__init__(coordinator)
        self._cam_id = cam_id
        cam = coordinator.data[cam_id]
        self._attr_unique_id = f"{DOMAIN}_{cam_id}_link"
        self._attr_name = cam["name"]
        self._attr_attribution = cam.get("attribution")
        self._attr_device_info = device_info_for(entry, cam.get("attribution"))

    @property
    def available(self) -> bool:
        return super().available and self._cam_id in self.coordinator.data

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data[self._cam_id].get("live_status")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        cam = self.coordinator.data[self._cam_id]
        return {
            "official_url": cam.get("official_url"),
            "route": cam.get("route"),
            "last_live_at": cam.get("last_live_at"),
            "attribution": cam.get("attribution"),
        }


class LiveCountSensor(CoordinatorEntity[CamsCoordinator], SensorEntity):
    """How many of the entry's cameras the site's last check saw live."""

    _attr_has_entity_name = True
    _attr_name = "Cameras live"
    _attr_icon = "mdi:check-network"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: CamsCoordinator, entry: LiveTrafficCamConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.slug}_live_count"
        first = next(iter(coordinator.data.values()), {})
        self._attr_device_info = device_info_for(entry, first.get("attribution"))

    @property
    def native_value(self) -> int:
        return sum(1 for c in self.coordinator.data.values() if c.get("live_status") == "live")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"total": len(self.coordinator.data)}
