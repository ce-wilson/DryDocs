"""Generate the software-registry UI view — the SOFT LINK between
config/taxonomy/software-registry.yaml and drydocs-icons/manifest.json
(user directive 2026-07-31).

Soft link means: vendors and icons are joined BY ID (vendor.icon override,
else vendor.id), a vendor with no icon renders without one and is listed in
``vendors_without_icons`` (reported, never silent, never an error), and
neither file gains a hard dependency on the other. Emits
``web/src/generated/software-registry.json`` and copies each matched icon's
display asset to ``web/public/vendor-icons/<icon-id>.<ext>`` so the Vite app
can serve it same-origin (the artifact CSP / self-contained rule).

Rides the default ``render_board.py`` run (the J17/J20/N4 one-entry-point
idiom); ``tests/unit/test_software_registry_json.py`` is the drift guard.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "config" / "taxonomy" / "software-registry.yaml"
MANIFEST = REPO / "drydocs-icons" / "manifest.json"
ICONS_ROOT = REPO / "drydocs-icons"
OUT = REPO / "web" / "src" / "generated" / "software-registry.json"
ASSET_DIR = REPO / "web" / "public" / "vendor-icons"


def _display_asset(icon: dict) -> str:
    """The manifest names one preferred display asset: ``raster`` when
    ``display: raster`` is set (e.g. ab-initio's block PNG), else the svg."""
    if icon.get("display") == "raster" and icon.get("raster"):
        return icon["raster"]
    return icon["svg"]


def build_software_registry_view() -> dict:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    icons = manifest["icons"]

    vendors, without_icons = [], []
    for v in registry["vendors"]:
        icon_id = v.get("icon", v["id"])  # the soft link: override, else convention
        icon = icons.get(icon_id)
        row = {
            "id": v["id"],
            "name": v["name"],
            "publisher_url": v["publisher_url"],
            "icon": None,
        }
        if icon is None:
            without_icons.append(v["id"])
        else:
            source = _display_asset(icon)
            row["icon"] = {
                "id": icon_id,
                "label": icon["label"],
                "kind": icon.get("kind"),  # software | product | infrastructure | persona
                "vendor": icon.get(
                    "vendor"
                ),  # owning brand when the icon is a product (e.g. jira -> atlassian)
                "category": icon.get("category"),
                "hex": icon.get("hex"),
                "verified": icon.get("verified", False),
                # served same-origin by the Vite app (web/public/)
                "asset": f"vendor-icons/{icon_id}{Path(source).suffix}",
                "source": source,  # repo path inside drydocs-icons/ (provenance)
            }
        vendors.append(row)

    products = [
        {
            "id": p["id"],
            "vendor": p["vendor"],
            "name": p["name"],
            "category": p.get("category"),
            "role": p.get("role"),
            "type": p.get("type"),
            "versions": p.get("versions", []),
            "used_by_drydocs": p.get("used_by_drydocs", False),
        }
        for p in registry["products"]
    ]

    return {
        "schema": "drydocs.software-registry-view.v1",
        "generated_from": [
            "config/taxonomy/software-registry.yaml",
            "drydocs-icons/manifest.json",
        ],
        "note": (
            "Soft link by id (vendor.icon override, else vendor.id). Vendors "
            "without a manifest icon are listed in vendors_without_icons — "
            "reported, never silent, never an error."
        ),
        "acronyms": registry.get("acronyms", {}),
        "drydocs_application_id": registry.get("drydocs_application_id"),
        "vendors": vendors,
        "vendors_without_icons": without_icons,
        "products": products,
    }


def copy_assets(view: dict) -> list[str]:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for v in view["vendors"]:
        if not v["icon"]:
            continue
        src = ICONS_ROOT / v["icon"]["source"]
        dst = REPO / "web" / "public" / v["icon"]["asset"]
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copyfile(src, dst)
        copied.append(v["icon"]["asset"])
    return copied


def main() -> None:
    view = build_software_registry_view()
    OUT.write_text(json.dumps(view, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    assets = copy_assets(view)
    print(
        f"wrote {OUT} ({len(view['vendors'])} vendors, {len(view['products'])} products, "
        f"{len(assets)} icon assets -> web/public/vendor-icons/, "
        f"{len(view['vendors_without_icons'])} without icons: "
        f"{', '.join(view['vendors_without_icons']) or 'none'})"
    )


if __name__ == "__main__":
    main()
