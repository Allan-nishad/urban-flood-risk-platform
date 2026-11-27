"""End-to-end tests for V8 Flood Alert Center, Automatic Alert Demo Mode, and Civilian Safety Page."""

from pathlib import Path
import urllib.request

from playwright.sync_api import sync_playwright

from floodrisk.dashboard.server import run_dashboard


def test_frontend_has_no_secrets_or_paid_api_keys():
    static_dir = Path("src/floodrisk/dashboard/static")
    for fname in ("index.html", "civilian-alert.html"):
        text = (static_dir / fname).read_text(encoding="utf-8")
        assert "maps.googleapis.com" not in text
        assert "textbee" not in text.lower()
        assert "supabase" not in text.lower()
        assert "firebase" not in text.lower()
        assert "AIza" not in text


def test_civilian_alert_page_served_directly():
    srv = run_dashboard(host="127.0.0.1", port=0, blocking=False)
    port = srv.server_address[1]
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/civilian-alert.html", timeout=5) as r:
            assert r.status == 200
            assert r.headers.get("X-Content-Type-Options") == "nosniff"
            html = r.read().decode("utf-8")
        assert "Bengaluru Citizen Safety" in html
        assert "tel:112" in html
        assert "SUGGESTED DEMONSTRATION DESTINATION" in html
        assert "ROUTES ARE INDICATIVE ONLY" in html
    finally:
        srv.shutdown()
        srv.server_close()


def test_playwright_automatic_alert_and_civilian_safety_flow():
    srv = run_dashboard(host="127.0.0.1", port=0, blocking=False)
    port = srv.server_address[1]
    base = f"http://127.0.0.1:{port}"
    errors = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1440, "height": 900})
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

            page.goto(base, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_selector("#autoAlertBtn")
            page.wait_for_function(
                "document.getElementById('zoneCardsGrid').innerText.includes('North Bengaluru')",
                timeout=15000,
            )

            # Verify all 4 zones are rendered
            zone_text = page.locator("#zoneCardsGrid").inner_text()
            for z in ("North Bengaluru", "South Bengaluru", "East Bengaluru", "West Bengaluru"):
                assert z in zone_text

            # Verify each severity & zone option exists in Automatic Alert modal
            page.click("#autoAlertBtn")
            assert page.is_visible("#autoAlertModal")
            for val in ("10", "20", "35", "50"):
                assert page.locator(f'#demoRainSelect option[value="{val}"]').count() == 1

            # Trigger East Bengaluru 50 mm/h Severe Demo Alert
            page.select_option("#demoZoneSelect", "East Bengaluru")
            page.select_option("#demoRainSelect", "50")
            page.click("#triggerDemoAlertBtn")

            # Verify Danger Popup, counter, history, and VIEW CIVILIAN ALERT button
            assert page.is_visible("#dangerAlertPopup")
            assert "DEMONSTRATION ALERT — SIMULATED DATA — NOT A REAL EMERGENCY" in page.inner_text("#dangerPopupSourceBadge")
            assert "EAST BENGALURU" in page.inner_text("#dangerPopupTitle")
            assert page.inner_text("#floodCenterActiveCount") == "1"
            assert page.is_visible("#viewCivilianAlertBtn")
            hist_text = page.inner_text("#unifiedAlertHistoryTbody")
            assert "East Bengaluru" in hist_text
            assert "DEMO" in hist_text

            # Acknowledge & Resolve demo alert, then Reset Demo
            page.click("#popupAckBtn")
            assert not page.is_visible("#dangerAlertPopup")
            assert "ACKNOWLEDGED" in page.inner_text("#unifiedAlertHistoryTbody")
            page.click("#facResetDemoBtn")
            assert page.inner_text("#floodCenterActiveCount") == "0"

            # Trigger again and verify VIEW CIVILIAN ALERT opens fixed URL
            page.click("#autoAlertBtn")
            page.select_option("#demoZoneSelect", "East Bengaluru")
            page.select_option("#demoRainSelect", "50")
            page.click("#triggerDemoAlertBtn")

            with ctx.expect_page() as civ_info:
                page.click("#viewCivilianAlertBtn")
            civ_page = civ_info.value
            civ_page.wait_for_load_state("domcontentloaded")
            assert "/civilian-alert.html" in civ_page.url
            assert "HEAVY RAINFALL WARNING — EAST BENGALURU" in civ_page.inner_text("#warnTitle")
            assert "SUGGESTED DEMONSTRATION DESTINATION" in civ_page.inner_text("#destList")
            assert civ_page.locator('#sosBtn[href="tel:112"]').count() == 1

            # Copy link fallback + SOS modal
            civ_page.click("#copyLinkBtn")
            assert "Alert link copied" in civ_page.inner_text("#copyFeedback")
            civ_page.click("#sosBtn")
            assert civ_page.is_visible("#sosModal")
            civ_page.click("#sosCancelBtn")

            # Independent fresh browser session + OSRM failure fallback test
            fresh_ctx = browser.new_context(viewport={"width": 1280, "height": 800})
            fresh_page = fresh_ctx.new_page()
            fresh_page.route("https://router.project-osrm.org/**", lambda route: route.abort())
            fresh_page.goto(f"{base}/civilian-alert.html", wait_until="domcontentloaded", timeout=20000)
            fresh_page.wait_for_timeout(800)
            assert "HEAVY RAINFALL WARNING — EAST BENGALURU" in fresh_page.inner_text("#warnTitle")
            assert "Route calculation is temporarily unavailable" in fresh_page.inner_text("#routeInfoBox")
            fresh_ctx.close()

            browser.close()
    finally:
        srv.shutdown()
        srv.server_close()

    assert errors == []
