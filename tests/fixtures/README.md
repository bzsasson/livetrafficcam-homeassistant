# Fixtures

Saved from livetrafficcam.com on 2026-09-18, then edited by hand so the
tests cover paths the live data did not show that day:

- `cams_snoqualmie_pass.json`: the last cam's `image` set to `null` (link-out
  path); the second-to-last cam's `live_status` set to `"stale"`.
- `events_snoqualmie_pass.json`: the first event set to `event_type:
  "closure"` with `is_full_closure: true`.
- `entities_wa.json`: one airport entity (`harvey-field-airport-washington`,
  kind `airport`) appended by hand, since airports joined the API after the
  save.
