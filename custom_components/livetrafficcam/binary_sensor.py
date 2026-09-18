"""Verified-live per cam; disruption and full-closure per entry."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import (
    CamsCoordinator,
    EventsCoordinator,
    LiveTrafficCamConfigEntry,
    device_info_for,
)

HEADLINES_SHOWN = 5


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LiveTrafficCamConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add verified-live per cam and the two disruption sensors."""
    rd = entry.runtime_data
    first = next(iter(rd.cams.data.values()), {})
    attribution = first.get("attribution")
    entities: list[BinarySensorEntity] = [
        VerifiedLiveSensor(rd.cams, entry, cam_id) for cam_id in rd.cams.data
    ]
    entities.append(DisruptionSensor(rd.events, entry, attribution))
    entities.append(FullClosureSensor(rd.events, entry, attribution))
    async_add_entities(entities)


class VerifiedLiveSensor(CoordinatorEntity[CamsCoordinator], BinarySensorEntity):
    """On when the site's liveness check last saw a current frame from this camera."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self, coordinator: CamsCoordinator, entry: LiveTrafficCamConfigEntry, cam_id: int
    ) -> None:
        super().__init__(coordinator)
        self._cam_id = cam_id
        cam = coordinator.data[cam_id]
        self._attr_unique_id = f"{DOMAIN}_{cam_id}_live"
        self._attr_name = f"{cam['name']} verified live"
        self._attr_device_info = device_info_for(entry, cam.get("attribution"))

    @property
    def available(self) -> bool:
        return super().available and self._cam_id in self.coordinator.data

    @property
    def is_on(self) -> bool:
        return self.coordinator.data[self._cam_id].get("live_status") == "live"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"last_live_at": self.coordinator.data[self._cam_id].get("last_live_at")}


class _EventsSensor(CoordinatorEntity[EventsCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self,
        coordinator: EventsCoordinator,
        entry: LiveTrafficCamConfigEntry,
        attribution: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._attr_device_info = device_info_for(entry, attribution)

    @property
    def _feed(self) -> dict[str, Any] | None:
        return (self.coordinator.data or {}).get("feed")

    @property
    def _events(self) -> list[dict[str, Any]]:
        return list((self.coordinator.data or {}).get("events") or [])

    @property
    def available(self) -> bool:
        # Never "all clear" while the feed is down or the state has no feed:
        # unavailable, not off. Same rule as the site's quiet line.
        feed = self._feed
        return super().available and bool(feed) and bool(feed.get("fresh"))


class DisruptionSensor(_EventsSensor):
    """On when the state's DOT feed reports anything inside this place."""

    _attr_name = "Disruption reported"

    def __init__(
        self,
        coordinator: EventsCoordinator,
        entry: LiveTrafficCamConfigEntry,
        attribution: str | None,
    ) -> None:
        super().__init__(coordinator, entry, attribution)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.slug}_disruption"

    @property
    def is_on(self) -> bool:
        return len(self._events) > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        feed = self._feed or {}
        events = self._events
        return {
            "count": len(events),
            "headlines": [e.get("headline") for e in events[:HEADLINES_SHOWN]],
            "agency": feed.get("agency"),
            "feed_fetched_at": feed.get("fetched_at"),
            "feed_fresh": feed.get("fresh"),
        }


class FullClosureSensor(_EventsSensor):
    """On when a reported event is a full closure."""

    _attr_name = "Full closure reported"

    def __init__(
        self,
        coordinator: EventsCoordinator,
        entry: LiveTrafficCamConfigEntry,
        attribution: str | None,
    ) -> None:
        super().__init__(coordinator, entry, attribution)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.slug}_closure"

    @property
    def _closures(self) -> list[dict[str, Any]]:
        return [e for e in self._events if e.get("is_full_closure")]

    @property
    def is_on(self) -> bool:
        return len(self._closures) > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        first = self._closures[0] if self._closures else None
        return {"headline": first.get("headline") if first else None}
