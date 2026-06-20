"""The furnishing symbol library (assets/furnishings) and AI-assisted pricing.

Loads manifest.json / groups.json, caches per-kind SVG renderers, and talks to
the Anthropic Messages API (standard library only) to refresh purchase prices.
"""
import json

from floorplanner.config import FURN_DIR, app_settings
from floorplanner.geometry import fmt_ftin

try:
    from PyQt6.QtSvg import QSvgRenderer
except ImportError:               # QtSvg missing: furnishings draw as boxes
    QSvgRenderer = None

__all__ = [
    "furnishing_catalog", "furnishing_spec", "furnishing_groups",
    "furnishing_renderer",
    "ANTHROPIC_API_URL", "ANTHROPIC_VERSION", "AI_PROVIDERS",
    "default_pricing_prompt", "parse_price_json", "anthropic_fetch_prices",
    "apply_furnishing_prices", "load_saved_api_key", "save_api_key",
]

_FURN_CATALOG = None
_FURN_GROUPS = None
_FURN_RENDERERS = {}


def furnishing_catalog() -> list:
    """The furnishing library: assets/furnishings/manifest.json entries
    (id, name, category, file, width_in, depth_in — true sizes in inches).
    Each SVG's viewBox is in inches too, so symbols render at real scale."""
    global _FURN_CATALOG
    if _FURN_CATALOG is None:
        _FURN_CATALOG = []
        try:
            entries = json.loads((FURN_DIR / "manifest.json")
                                 .read_text(encoding="utf-8"))
        except (OSError, ValueError):
            entries = []
        for ent in entries:
            try:
                spec = {
                    "id": str(ent["id"]),
                    "name": str(ent.get("name", ent["id"])),
                    "category": str(ent.get("category", "Misc")),
                    "file": str(ent["file"]),
                    "width_in": float(ent["width_in"]),
                    "depth_in": float(ent["depth_in"]),
                    "price": float(ent.get("price", 0.0) or 0.0),
                }
            except (KeyError, TypeError, ValueError):
                continue
            if (FURN_DIR / spec["file"]).is_file():
                _FURN_CATALOG.append(spec)
    return _FURN_CATALOG


def furnishing_spec(kind: str):
    for spec in furnishing_catalog():
        if spec["id"] == kind:
            return spec
    return None


def furnishing_groups() -> list:
    """Palette sections from assets/furnishings/groups.json:
    [{"name", "specs"}], in file order.  Items are SVG file names (ids
    also accepted); unknown names are skipped and a furnishing may sit
    in several groups.  The "All" group always holds the whole catalog.
    Without a usable groups.json, falls back to All + the manifest
    categories."""
    global _FURN_GROUPS
    if _FURN_GROUPS is None:
        cat = furnishing_catalog()
        by_name = {s["file"]: s for s in cat}
        by_name.update({s["id"]: s for s in cat})
        sections = []
        try:
            entries = json.loads((FURN_DIR / "groups.json")
                                 .read_text(encoding="utf-8"))
        except (OSError, ValueError):
            entries = []
        for ent in entries if isinstance(entries, list) else []:
            name = str(ent.get("name", "")).strip()
            if not name:
                continue
            if name.lower() == "all":
                specs = list(cat)
            else:
                specs = []
                for raw in ent.get("items", []):
                    spec = by_name.get(str(raw))
                    if spec is not None and spec not in specs:
                        specs.append(spec)
            if specs:
                sections.append({"name": name, "specs": specs})
        if not sections:
            sections = [{"name": "All", "specs": list(cat)}]
            by_cat = {}
            for s in cat:
                by_cat.setdefault(s["category"], []).append(s)
            sections += [{"name": k, "specs": v} for k, v in by_cat.items()]
        _FURN_GROUPS = sections
    return _FURN_GROUPS


def furnishing_renderer(kind: str):
    """Shared QSvgRenderer for a furnishing kind (None if unavailable)."""
    if QSvgRenderer is None:
        return None
    if kind not in _FURN_RENDERERS:
        spec = furnishing_spec(kind)
        if spec is None:
            return None
        _FURN_RENDERERS[kind] = QSvgRenderer(str(FURN_DIR / spec["file"]))
    r = _FURN_RENDERERS[kind]
    return r if r.isValid() else None


# ----------------------------------------------------------------------------
# AI-assisted pricing — ask a model for current furnishing purchase prices
# and write them into manifest.json's `price` field.
# ----------------------------------------------------------------------------
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# AI systems offered in the AI ▸ Update prices… dialog drop-down.
AI_PROVIDERS = [
    {"name": "Anthropic Claude",
     "models": ["claude-sonnet-4-6", "claude-opus-4-8",
                "claude-haiku-4-5-20251001"]},
]


def default_pricing_prompt(catalog=None) -> str:
    """The editable prompt pre-filled into the pricing dialog: lists every
    catalog item and asks for a single current US retail price each, returned
    as a strict JSON object {id: dollars}."""
    if catalog is None:
        catalog = furnishing_catalog()
    lines = [f'{s["id"]}\t{s["name"]} '
             f'({fmt_ftin(s["width_in"])} x {fmt_ftin(s["depth_in"])}, '
             f'{s["category"]})'
             for s in catalog]
    return (
        "You are a procurement assistant pricing home furnishings and "
        "fixtures.\n"
        "For each catalog item below, give a single representative CURRENT "
        "US retail purchase price for a new, mid-range product, in US "
        "dollars.\n\n"
        "Respond with ONLY a JSON object that maps each item id to a number "
        "(plain dollars, no currency symbols, no ranges, no commentary and "
        "no markdown fences). Example: {\"sofa\": 899, \"toilet\": 180}\n\n"
        "Items (id <tab> description):\n" + "\n".join(lines) + "\n")


def parse_price_json(text: str) -> dict:
    """Extract a {id: float-price} mapping from an AI text reply, tolerating
    surrounding prose or ```json fences. Raises RuntimeError if nothing
    usable is found."""
    s = (text or "").strip()
    a, b = s.find("{"), s.rfind("}")
    if a == -1 or b == -1 or b < a:
        raise RuntimeError("No JSON object found in the AI reply.")
    try:
        obj = json.loads(s[a:b + 1])
    except ValueError as ex:
        raise RuntimeError(f"Could not parse the AI reply as JSON: {ex}") \
            from ex
    out = {}
    for key, val in (obj.items() if isinstance(obj, dict) else []):
        try:
            out[str(key)] = float(val)
        except (TypeError, ValueError):
            continue
    if not out:
        raise RuntimeError("The AI reply contained no usable prices.")
    return out


def anthropic_fetch_prices(api_key: str, model: str, prompt: str,
                           *, timeout: float = 60.0) -> dict:
    """POST the prompt to the Anthropic Messages API and return the parsed
    {id: price} mapping. Raises RuntimeError on any network/API failure.
    Uses only the standard library (no SDK dependency)."""
    import urllib.error
    import urllib.request
    body = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(ANTHROPIC_API_URL, data=body, method="POST")
    req.add_header("content-type", "application/json")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", ANTHROPIC_VERSION)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        detail = ex.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"API error {ex.code}: {detail}") from ex
    except (urllib.error.URLError, TimeoutError, OSError) as ex:
        raise RuntimeError(f"Could not reach the AI service: {ex}") from ex
    except ValueError as ex:
        raise RuntimeError(f"Unexpected reply from the AI service: {ex}") \
            from ex
    text = "".join(blk.get("text", "") for blk in payload.get("content", [])
                   if isinstance(blk, dict) and blk.get("type") == "text")
    return parse_price_json(text)


def apply_furnishing_prices(prices: dict) -> int:
    """Write {id: price} into manifest.json and the live catalog in place.
    Returns the number of catalog items whose price was set."""
    path = FURN_DIR / "manifest.json"
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        entries = []
    if isinstance(entries, list):
        for ent in entries:
            if isinstance(ent, dict) and str(ent.get("id")) in prices:
                ent["price"] = float(prices[str(ent["id"])])
        path.write_text(json.dumps(entries, indent=2) + "\n",
                        encoding="utf-8")
    n = 0
    for spec in furnishing_catalog():
        if spec["id"] in prices:
            spec["price"] = float(prices[spec["id"]])
            n += 1
    return n


def load_saved_api_key() -> str:
    """The Anthropic API key remembered in the settings file, if any."""
    try:
        return str(app_settings().value("anthropic_api_key", "") or "")
    except Exception:                       # noqa: BLE001 - best effort
        return ""


def save_api_key(key: str) -> None:
    try:
        app_settings().setValue("anthropic_api_key", key)
    except Exception:                       # noqa: BLE001 - best effort
        pass
