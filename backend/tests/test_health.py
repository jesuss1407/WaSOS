"""Insignia "API viva" (Kiro IAthon): GET /health pública, 200 y {"status":"ok","team":TEAM_ID}."""
import json
import os

import app


def test_health():
    r = app.handler({"routeKey": "GET /health", "headers": {}}, None)  # sin X-Admin-Key
    assert r["statusCode"] == 200
    assert r["headers"]["Content-Type"].startswith("application/json")
    assert json.loads(r["body"]) == {"status": "ok", "team": os.environ["TEAM_ID"]}
