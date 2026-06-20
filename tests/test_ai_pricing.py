"""AI-assisted furnishing pricing: prompt building, reply parsing, and the
manifest/catalog write-back.  No network is touched -- the Anthropic call is
monkeypatched -- so these run headless and offline."""

import json

import pytest

pytestmark = pytest.mark.furnishings


@pytest.fixture
def manifest_guard(fp):
    """Back up manifest.json and restore it (and the cached catalog) after a
    test mutates prices, so the repo file is never left dirty."""
    path = fp.FURN_DIR / "manifest.json"
    original = path.read_text(encoding="utf-8")
    yield path
    path.write_text(original, encoding="utf-8")
    from floorplanner import catalog
    catalog._FURN_CATALOG = None     # force a clean reload of the catalog


def test_catalog_carries_price_field(fp):
    for spec in fp.furnishing_catalog():
        assert "price" in spec
        assert isinstance(spec["price"], float)


def test_default_prompt_lists_items_and_requests_json(fp):
    prompt = fp.default_pricing_prompt()
    assert "JSON" in prompt
    ids = [s["id"] for s in fp.furnishing_catalog()]
    assert ids[0] in prompt and ids[-1] in prompt


def test_parse_price_json_plain(fp):
    out = fp.parse_price_json('{"sofa": 899, "toilet": 180.5}')
    assert out == {"sofa": 899.0, "toilet": 180.5}


def test_parse_price_json_tolerates_prose_and_fences(fp):
    text = 'Sure!\n```json\n{"sofa": 1200}\n```\nHope that helps.'
    assert fp.parse_price_json(text) == {"sofa": 1200.0}


def test_parse_price_json_rejects_garbage(fp):
    with pytest.raises(RuntimeError):
        fp.parse_price_json("no json here")
    with pytest.raises(RuntimeError):
        fp.parse_price_json('{"a": "not-a-number"}')


def test_apply_prices_updates_manifest_and_catalog(fp, manifest_guard):
    ids = [s["id"] for s in fp.furnishing_catalog()[:2]]
    n = fp.apply_furnishing_prices({ids[0]: 100.0, ids[1]: 250.0})
    assert n == 2
    assert fp.furnishing_spec(ids[0])["price"] == 100.0
    man = json.loads(manifest_guard.read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in man}
    assert by_id[ids[1]]["price"] == 250.0


def test_placed_item_picks_up_price(fp, scene, manifest_guard):
    ids = [s["id"] for s in fp.furnishing_catalog()[:1]]
    fp.apply_furnishing_prices({ids[0]: 555.0})
    from PyQt6.QtCore import QPointF
    it = fp.FurnishingItem(ids[0], QPointF(50, 50), 0)
    assert it.price == 555.0


def test_dialog_has_provider_model_and_prefilled_prompt(fp, qapp):
    dlg = fp.AIPricingDialog()
    assert dlg.cb_provider.count() == len(fp.AI_PROVIDERS)
    assert dlg.cb_provider.itemText(0) == "Anthropic Claude"
    assert dlg.cb_model.count() >= 1
    assert "JSON" in dlg.ed_prompt.toPlainText()


def test_dialog_fetch_applies_without_network(fp, qapp, monkeypatch,
                                              manifest_guard):
    ids = [s["id"] for s in fp.furnishing_catalog()[:1]]
    # AIPricingDialog._fetch resolves the name in the dialogs module, so patch
    # it there (where it is used), not on the FloorPlanner shim.
    from floorplanner import dialogs
    monkeypatch.setattr(dialogs, "anthropic_fetch_prices",
                        lambda *a, **k: {ids[0]: 42.0})
    dlg = fp.AIPricingDialog()
    dlg.ed_key.setText("sk-ant-test")
    dlg._fetch()
    assert dlg.result_prices == {ids[0]: 42.0}
    assert dlg.result() == fp.QDialog.DialogCode.Accepted
