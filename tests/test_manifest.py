"""The manifest and the constants must agree."""

import json
from pathlib import Path

from custom_components.livetrafficcam.const import DOMAIN, VERSION

MANIFEST = Path(__file__).parent.parent / "custom_components" / "livetrafficcam" / "manifest.json"


def test_manifest_matches_constants():
    m = json.loads(MANIFEST.read_text())
    assert m["domain"] == DOMAIN
    assert m["version"] == VERSION
    required = (
        "name", "codeowners", "documentation", "issue_tracker", "iot_class", "integration_type",
    )
    for key in required:
        assert m[key]
    assert m["config_flow"] is True
