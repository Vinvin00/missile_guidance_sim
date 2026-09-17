"""Guard the production wiring that previously differed between branches."""

import json
from pathlib import Path
from urllib.parse import urlparse

from fastapi.testclient import TestClient

from guidance_sim.api.main import app

ROOT = Path(__file__).resolve().parents[1]


def test_vercel_builds_the_frontend_from_the_repository_root():
    config = json.loads((ROOT / "vercel.json").read_text())
    assert config["framework"] == "vite"
    assert config["installCommand"] == "cd frontend && npm ci"
    assert config["buildCommand"] == "cd frontend && npm run build"
    assert config["outputDirectory"] == "frontend/dist"
    assert (ROOT / "frontend/package-lock.json").is_file()


def test_production_urls_match_the_frontend_consumers():
    env = dict(
        line.split("=", 1)
        for line in (ROOT / "frontend/.env.production").read_text().splitlines()
        if line and not line.startswith("#")
    )
    assert urlparse(env["VITE_API_BASE_URL"]).scheme == "https"
    assert urlparse(env["VITE_AERO_RAG_API_URL"]).scheme == "https"
    websocket = urlparse(env["VITE_WS_URL"])
    assert websocket.scheme == "wss"
    assert websocket.netloc == urlparse(env["VITE_API_BASE_URL"]).netloc
    assert websocket.path == "/ws/trajectory"
    panel = (ROOT / "frontend/src/components/SpecGroundingPanel.jsx").read_text()
    assert "import.meta.env.VITE_AERO_RAG_API_URL" in panel
    assert "branch: main" in (ROOT / "render.yaml").read_text()


def test_production_aliases_can_fetch_the_catalog():
    client = TestClient(app)
    for origin in (
        "https://physics-sim-green.vercel.app",
        "https://physics-sim-vincenzos-projects-d7ceae2a.vercel.app",
        "https://physics-sim-git-main-vincenzos-projects-d7ceae2a.vercel.app",
    ):
        response = client.get("/api/catalog", headers={"Origin": origin})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
