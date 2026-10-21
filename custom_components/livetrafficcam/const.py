"""Constants for the Live Traffic Cam integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "livetrafficcam"
VERSION = "1.1.0"
BASE_URL = "https://livetrafficcam.com"
USER_AGENT = (
    f"livetrafficcam-homeassistant/{VERSION} "
    "(+https://github.com/bzsasson/livetrafficcam-homeassistant)"
)

CAMS_INTERVAL = timedelta(minutes=5)
EVENTS_INTERVAL = timedelta(minutes=10)
IMAGE_HOLD_SECONDS = 60
MAX_IMAGE_BYTES = 4 * 1024 * 1024
HIGHWAY_MAX_CAMS = 25
# Point places: every camera preselected. Airports (FAA weather cams) joined
# the entities API on 2026-09-18. Highways ("corridor") get the picker, and
# so do metro areas and cities, which joined the API on 2026-10-21.
FEATURE_KINDS = ("pass", "bridge", "tunnel", "airport")
PICK_KINDS = ("corridor", "metro", "city")
# Cities live in the site's places table: cams.json reads them through
# ?place= and they have no event feed, so a city entry gets no disruption
# sensors.
CITY_KIND = "city"

CONF_STATE = "state"
CONF_SLUG = "slug"
CONF_NAME = "name"
CONF_KIND = "kind"
CONF_ROUTE = "route"
CONF_PAGE = "page"
CONF_CAM_IDS = "cam_ids"

PLATFORMS = [Platform.CAMERA, Platform.SENSOR, Platform.BINARY_SENSOR]

# The site has no state-list endpoint; the list is static. Not every state
# has entities: the config flow's entity step handles an empty answer.
US_STATES: dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
