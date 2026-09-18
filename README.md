# Live Traffic Cam for Home Assistant

Put a mountain pass, bridge, tunnel or highway on your dashboard: the
latest still from each official DOT camera, a verified-live sensor per
camera, a cameras-live count, and reported disruptions for that place.
Data comes from [livetrafficcam.com](https://livetrafficcam.com), which
checks every camera's feed on a schedule and relays the state DOT's own
incident and closure reports.

No API keys. Pick a state, pick a place, pick cameras, done.

## What you get

For every configured place (one config entry each):

- `camera.*` for each camera that livetrafficcam.com may show inline.
  Attributes: `live_status`, `last_live_at`, `route`, `official_url`,
  and the agency attribution.
- `binary_sensor.* verified live` for each camera: on when the site's
  last check saw a current frame. Use it to hide stale cameras or to
  get a notification when a pass goes dark.
- `sensor.* cameras live`: how many of the place's cameras are live.
- `binary_sensor.* disruption reported` and `full closure reported`,
  from the DOT's own event feed. They read unavailable, not off, when
  the feed is stale, because a quiet sensor on a dead feed would lie.
- Cameras whose agency only allows linking appear as a sensor with the
  agency's own page URL, never as an image.

The device page links to the place's page on livetrafficcam.com, for
example [Snoqualmie Pass](https://livetrafficcam.com/traffic-cameras/washington/snoqualmie-pass/).
Camera reliability across states is on the
[camera uptime report](https://livetrafficcam.com/reports/camera-uptime/).

## Install

Through HACS: add `https://github.com/bzsasson/livetrafficcam-homeassistant`
as a custom repository (type Integration), install, restart, then
Settings > Devices & services > Add integration > Live Traffic Cam.

Manually: copy `custom_components/livetrafficcam` into your
`config/custom_components/` and restart.

## Coverage and limits

- States with inline images as of September 2026: Washington,
  California, Utah, Nevada, Arizona, Georgia, Wisconsin, Alaska, Idaho,
  Iowa. The list grows with the site; the state dropdown shows every
  state and says when one has nothing yet.
- Highways can have hundreds of cameras; the flow asks you to pick up
  to 25. Passes, bridges and tunnels come with all their cameras.
- Stills refresh at most once a minute per camera; camera data every
  five minutes; disruptions every ten. No video in this version.
- If you want travel times, or incidents from a 511 system you hold a
  key for, [The 511](https://github.com/ihavespoken327/ha-the511) is the
  better fit. This one needs no keys.

## About

Built by the person who runs livetrafficcam.com. Images stay on the
agencies' terms: the site shows a camera inline only where the source
allows it, and this integration follows the same rule by construction.
Issues and ideas go in the tracker on this repo.
