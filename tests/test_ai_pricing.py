"""AI-assisted furnishing pricing: prompt building, reply parsing, and the
manifest/catalog write-back.  No network is touched -- the Anthropic call is
monkeypatched -- so these run headless and offline."""

import json

import pytest

pytestmark = pytest.mark.furnishings


@pytest.fixture
def price_sandbox(fp, tmp_path, monkeypatch):
    """Redirect the user price-overrides file to a tmp path (P0.5 fix 5:
    apply_furnishing_prices now writes there, never the bundled manifest) and
    reset the cached catalog. Yields (override_path, manifest_path,
    manifest_bytes_before) so tests can assert the manifest stays untouched."""
    from floorplanner import catalog
    override = tmp_path / "furnishing_prices.json"
    monkeypatch.setattr(catalog, "_price_overrides_path", lambda: override)
    catalog._FURN_CATALOG = None         # reload so overrides are applied
    manifest = fp.FURN_DIR / "manifest.json"
    before = manifest.read_text(encoding="utf-8")
    yield override, manifest, before
    catalog._FURN_CATALOG = None         # clean reload for later tests


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


def test_apply_prices_writes_config_not_manifest(fp, price_sandbox):
    # REWRITTEN at P0.5 fix 5 (review §1): previously asserted the DEFECT -- that
    # apply_furnishing_prices writes into assets/furnishings/manifest.json, a
    # generated asset. It must persist to the per-user config dir and leave the
    # manifest byte-for-byte unchanged.
    override, manifest, before = price_sandbox
    ids = [s["id"] for s in fp.furnishing_catalog()[:2]]
    n = fp.apply_furnishing_prices({ids[0]: 100.0, ids[1]: 250.0})
    assert n == 2
    assert fp.furnishing_spec(ids[0])["price"] == 100.0        # live catalog set
    assert manifest.read_text(encoding="utf-8") == before      # manifest untouched
    saved = json.loads(override.read_text(encoding="utf-8"))   # persisted to config
    assert saved[ids[1]] == 250.0


def test_price_override_reloads_from_config(fp, price_sandbox):
    # a fresh catalog load merges the config overrides over the manifest price
    override, _manifest, _before = price_sandbox
    ids = [s["id"] for s in fp.furnishing_catalog()[:1]]
    fp.apply_furnishing_prices({ids[0]: 321.0})
    from floorplanner import catalog
    catalog._FURN_CATALOG = None                               # force a reload
    assert fp.furnishing_spec(ids[0])["price"] == 321.0


def test_placed_item_picks_up_price(fp, scene, price_sandbox):
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
                                              price_sandbox):
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
