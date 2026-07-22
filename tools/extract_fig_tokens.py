"""Extract design tokens from a Figma .fig local save into versioned JSON.

Usage:
    python tools/extract_fig_tokens.py <path/to/file.fig> [--version 1.6]

Outputs (git-tracked, diff-friendly — keys sorted, values normalized):
    src/frdqa/data/design-tokens-<version>.json      colors / typography / effects / grids
    src/frdqa/data/design-components-<version>.json  component (SYMBOL) index

The .fig binary is decoded with the kiwi parser vendored from
sketch-hq/fig2sketch (MIT, see tools/vendor/LICENSE-fig2sketch).
Requires: pip install zstandard  (zstd C-extension is NOT needed — see vendor/zstd.py shim)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
import kiwi  # noqa: E402  (vendored)

REPO = Path(__file__).resolve().parents[1]
DATA_DIR = REPO / "src" / "frdqa" / "data"

TYPE_CONVERTERS = {
    "GUID": lambda x: f"{x['sessionID']}:{x['localID']}",
    "Matrix": lambda m: [[m["m00"], m["m01"], m["m02"]], [m["m10"], m["m11"], m["m12"]]],
}


def hex_color(c: dict) -> str:
    return "#%02X%02X%02X" % (round(c["r"] * 255), round(c["g"] * 255), round(c["b"] * 255))


def platform_of(name: str) -> str | None:
    for seg in name.split("/"):
        seg = seg.strip().lower()
        if seg in ("pc", "desktop", "tablet", "mobile"):
            return seg
    return None


def unit_value(v: dict | None) -> dict | None:
    if not isinstance(v, dict):
        return None
    out = {}
    if "value" in v:
        out["value"] = round(v["value"], 4)
    if "units" in v:
        out["units"] = v["units"]
    return out or None


def collect(nodes: list[dict]) -> tuple[dict, dict, dict, dict, list, list]:
    colors: dict[str, dict] = {}
    typography: dict[str, dict] = {}
    effects: dict[str, dict] = {}
    grids: dict[str, dict] = {}
    conflicts: list[dict] = []

    def put(bucket: dict, name: str, token: dict, node_id: str):
        if name in bucket:
            prev = {k: v for k, v in bucket[name].items() if k != "figma_nodes"}
            cur = {k: v for k, v in token.items() if k != "figma_nodes"}
            if prev != cur:
                conflicts.append({"name": name, "kept": prev, "dropped": cur, "node": node_id})
            else:
                bucket[name]["figma_nodes"].append(node_id)
            return
        token["figma_nodes"] = [node_id]
        bucket[name] = token

    for n in nodes:
        style_type = n.get("styleType")
        if not style_type:
            continue
        name = (n.get("name") or "").strip()
        if not name:
            continue
        node_id = str(n.get("guid", "?"))

        if style_type == "FILL":
            paints = []
            for p in n.get("fillPaints", []):
                if p.get("type") == "SOLID" and "color" in p:
                    paint = {"$type": "color", "$value": hex_color(p["color"])}
                    a = p["color"].get("a", 1)
                    op = p.get("opacity", 1)
                    alpha = round(a * op, 4)
                    if alpha < 1:
                        paint["alpha"] = alpha
                    paints.append(paint)
                elif p.get("type"):
                    paints.append({"$type": p["type"].lower()})
            if len(paints) == 1:
                put(colors, name, paints[0], node_id)
            elif paints:
                put(colors, name, {"$type": "composite", "paints": paints}, node_id)

        elif style_type == "TEXT":
            fn = n.get("fontName", {})
            token = {
                "$type": "typography",
                "family": fn.get("family"),
                "style": fn.get("style"),
                "size": n.get("fontSize"),
                "lineHeight": unit_value(n.get("lineHeight")),
                "letterSpacing": unit_value(n.get("letterSpacing")),
                "platform": platform_of(name),
            }
            token = {k: v for k, v in token.items() if v is not None}
            put(typography, name, token, node_id)

        elif style_type == "EFFECT":
            effs = []
            for e in n.get("effects", []):
                eff = {"type": e.get("type")}
                if "color" in e:
                    eff["color"] = hex_color(e["color"])
                    a = e["color"].get("a", 1)
                    if a < 1:
                        eff["alpha"] = round(a, 4)
                if "offset" in e:
                    eff["offset"] = [e["offset"].get("x"), e["offset"].get("y")]
                for k in ("radius", "spread"):
                    if k in e:
                        eff[k] = e[k]
                effs.append(eff)
            put(effects, name, {"$type": "effect", "effects": effs}, node_id)

        elif style_type == "GRID":
            gs = []
            for g in n.get("layoutGrids", []):
                grid = {k: g.get(k) for k in ("pattern", "sectionSize", "gutterSize", "numSections", "axis") if k in g}
                gs.append(grid)
            put(grids, name, {"$type": "grid", "grids": gs}, node_id)

    # component (SYMBOL) index with resolved parent paths
    by_guid = {str(n["guid"]): n for n in nodes if "guid" in n}

    def path_of(n: dict) -> str:
        parts = []
        cur = n
        for _ in range(20):
            nm = (cur.get("name") or "").strip()
            if nm:
                parts.append(nm)
            pi = cur.get("parentIndex")
            pg = str(pi.get("guid")) if isinstance(pi, dict) else None
            cur = by_guid.get(pg) if pg else None
            if cur is None or cur.get("type") in ("CANVAS", "DOCUMENT"):
                break
        return " / ".join(reversed(parts))

    components = sorted(
        {path_of(n) for n in nodes if n.get("type") == "SYMBOL"}
    )
    return colors, typography, effects, grids, components, conflicts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("fig_path", type=Path)
    ap.add_argument("--version", default="1.6", help="design system version tag for output filenames")
    args = ap.parse_args()

    raw = args.fig_path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()

    with zipfile.ZipFile(args.fig_path) as z:
        exported_at = None
        if "meta.json" in z.namelist():
            exported_at = json.loads(z.read("meta.json")).get("exported_at")
        msg = kiwi.decode(z.open("canvas.fig"), TYPE_CONVERTERS)

    nodes = msg.get("nodeChanges", [])
    colors, typography, effects, grids, components, conflicts = collect(nodes)

    meta = {
        "design_system_version": args.version,
        "source": {
            "file": args.fig_path.name,
            "sha256": sha,
            "size_bytes": len(raw),
            "figma_exported_at": exported_at,
        },
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "extractor": "tools/extract_fig_tokens.py",
        "counts": {
            "nodes": len(nodes),
            "colors": len(colors),
            "typography": len(typography),
            "effects": len(effects),
            "grids": len(grids),
            "components": len(components),
            "conflicts": len(conflicts),
        },
    }

    tokens_out = {
        "meta": meta,
        "colors": colors,
        "typography": typography,
        "effects": effects,
        "grids": grids,
        "conflicts": conflicts,
    }
    comps_out = {"meta": meta, "components": components}

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tokens_path = DATA_DIR / f"design-tokens-v{args.version}.json"
    comps_path = DATA_DIR / f"design-components-v{args.version}.json"
    tokens_path.write_text(
        json.dumps(tokens_out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    comps_path.write_text(
        json.dumps(comps_out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {tokens_path}")
    print(f"wrote {comps_path}")
    print(json.dumps(meta["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
