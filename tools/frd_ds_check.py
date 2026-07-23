"""FRD ↔ Design System 정합 검사 (요소 단위, 명확한 불일치만 보고).

Usage:
    python tools/frd_ds_check.py <FRD.pdf> [--title "Rubicon 3.0 v1.4.8"]

각 요소(ID, Global Name)의 Description에서 색상·폰트·그림자 명세를 추출해
design-tokens와 대조하고, 결과를 단순한 HTML 한 장으로 낸다:
    reports/<pdf명>_DS-Conformance.html  (+ reports/data/<pdf명>_ds-conformance.json)
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[1]
TOKENS_PATH = REPO / "src" / "frdqa" / "data" / "design-tokens-v1.6.json"
ID_RE = re.compile(r"^\s*([A-Z]{1,2}\d+\.\d+)\s*$")
HEX_RE = re.compile(r"#([0-9A-Fa-f]{6})\b")
FONT_RE = re.compile(r"Samsung\s*(One|Sharp\s*Sans)(?:\s*Bold)?\s*(\d{3})?,?\s*(\d{1,2})\s*(?:pt|px)", re.I)
SHADOW_RE = re.compile(
    r"Drop Shadow:\s*X:\s*([\d.-]+),?\s*Y:\s*([\d.-]+),?\s*Blur:\s*([\d.-]+),?\s*Spread:\s*([\d.-]+),?"
    r"\s*Color:\s*#([0-9A-Fa-f]{6})\s*\(Opacity:\s*(\d+)%\)", re.I)


# ── 요소 추출 ──────────────────────────────────────────────────────────
def extract_elements(pdf_path: Path) -> tuple[list[dict], int]:
    doc = fitz.open(pdf_path)
    elements = []
    for i in range(doc.page_count):
        page = doc[i]
        spans = []
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    if s["text"].strip():
                        spans.append({"t": s["text"].strip(), "x": s["bbox"][0], "y": s["bbox"][1]})
        tables = []
        for h in (s for s in spans if s["t"] == "ID"):
            gn = next((s for s in spans if s["t"].startswith("Global Name") and abs(s["y"] - h["y"]) < 8), None)
            dd = next((s for s in spans if s["t"].startswith("Design Description") and abs(s["y"] - h["y"]) < 8), None)
            if gn:
                tables.append({"y": h["y"], "id_x": h["x"], "gn_x": gn["x"],
                               "dd_x": dd["x"] if dd else gn["x"] + 250})
        W = page.rect.width

        def clip(x0, y0, x1, y1):
            return re.sub(r"\s+", " ", page.get_text("text", clip=fitz.Rect(x0, y0, x1, y1))).strip()

        for ti, tb in enumerate(tables):
            y_top = tb["y"] + 24
            y_bot = tables[ti + 1]["y"] - 10 if ti + 1 < len(tables) else page.rect.height
            id_cells = sorted(
                (s for s in spans if ID_RE.match(s["t"]) and abs(s["x"] - tb["id_x"]) < 40 and y_top < s["y"] < y_bot),
                key=lambda s: s["y"])
            for ri, idc in enumerate(id_cells):
                r_top = y_top if ri == 0 else (id_cells[ri - 1]["y"] + idc["y"]) / 2 + 6
                r_bot = (idc["y"] + id_cells[ri + 1]["y"]) / 2 + 6 if ri + 1 < len(id_cells) else y_bot
                elements.append({
                    "page": i + 1,
                    "id": idc["t"],
                    "global_name": clip(tb["gn_x"] - 8, r_top, tb["dd_x"] - 8, r_bot),
                    "desc": clip(tb["dd_x"] - 8, r_top, W, r_bot),
                })
    n_pages = doc.page_count
    doc.close()
    return elements, n_pages


# ── 토큰 대조 ──────────────────────────────────────────────────────────
def load_tokens() -> dict:
    t = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
    hex2name = {}
    for name, v in t["colors"].items():
        if isinstance(v, dict) and str(v.get("$value", "")).startswith("#"):
            hex2name.setdefault(v["$value"].upper(), name)
    typo = set()
    typo_by_family = {}
    for name, v in t["typography"].items():
        if isinstance(v, dict):
            fam = "".join(str(v.get("family", "")).lower().split())
            key = (fam, str(v.get("style", "")), float(v.get("size") or 0))
            typo.add(key)
            typo_by_family.setdefault((fam, str(v.get("style", ""))), []).append((float(v.get("size") or 0), name))
    shadows = []
    for name, v in t["effects"].items():
        e = v["effects"][0]
        shadows.append({"name": name, "x": e["offset"][0], "y": e["offset"][1],
                        "blur": e["radius"], "spread": e.get("spread", 0),
                        "color": e["color"].upper(), "alpha": e.get("alpha", 1)})
    return {"hex2name": hex2name, "typo": typo, "typo_by_family": typo_by_family, "shadows": shadows}


def nearest_color(hexv: str, hex2name: dict) -> str:
    r, g, b = (int(hexv[i:i + 2], 16) for i in (1, 3, 5))
    best, bd = None, 1e9
    for h, name in hex2name.items():
        r2, g2, b2 = (int(h[i:i + 2], 16) for i in (1, 3, 5))
        d = (r - r2) ** 2 + (g - g2) ** 2 + (b - b2) ** 2
        if d < bd:
            bd, best = d, f"{name} {h}"
    return best or "-"


def check_element(el: dict, tk: dict) -> list[dict]:
    desc = el["desc"]
    findings = []
    for m in HEX_RE.finditer(desc):
        h = "#" + m.group(1).upper()
        if h not in tk["hex2name"]:
            findings.append({"kind": "색상", "frd": h,
                             "expected": f"승인 팔레트에 없음 (가장 가까운 토큰: {nearest_color(h, tk['hex2name'])})",
                             "fix": "승인 토큰으로 교체 또는 신규 토큰 등록"})
    for m in FONT_RE.finditer(desc):
        fam = "samsungone" if m.group(1).lower().startswith("one") else "samsungsharpsans"
        weight = m.group(2) or "Bold"
        size = float(m.group(3))
        if (fam, weight, size) not in tk["typo"]:
            sizes = sorted({s for s, _ in tk["typo_by_family"].get((fam, weight), [])})
            findings.append({"kind": "폰트", "frd": f"{m.group(0)}",
                             "expected": f"{fam} {weight} 승인 사이즈: {[int(s) for s in sizes]}",
                             "fix": "승인 타입스케일로 교체"})
    for m in SHADOW_RE.finditer(desc):
        x, y, blur, spread = (float(m.group(k)) for k in (1, 2, 3, 4))
        color, op = "#" + m.group(5).upper(), int(m.group(6)) / 100
        hit = any(s["x"] == x and s["y"] == y and s["blur"] == blur and s["spread"] == spread
                  and s["color"] == color and abs(s["alpha"] - op) < 0.005 for s in tk["shadows"])
        if not hit:
            near = min(tk["shadows"], key=lambda s: abs(s["x"] - x) + abs(s["y"] - y) + abs(s["blur"] - blur))
            findings.append({"kind": "그림자", "frd": f"X{x:g} Y{y:g} Blur{blur:g} Spread{spread:g} {color} {int(op*100)}%",
                             "expected": f"가장 가까운 토큰 {near['name']}: X{near['x']:g} Y{near['y']:g} Blur{near['blur']:g} Spread{near['spread']:g} {near['color']} {int(near['alpha']*100)}%",
                             "fix": f"{near['name']} 토큰 값으로 통일"})
    # 요소 내 중복 제거
    uniq, seen = [], set()
    for f in findings:
        k = (f["kind"], f["frd"])
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    return uniq


# ── HTML ──────────────────────────────────────────────────────────────
def esc(s):
    return html.escape(str(s), quote=False)


def render_html(title: str, meta: dict, bad: list[dict], ok: list[dict]) -> str:
    rows = []
    for e in bad:
        first = True
        for f in e["findings"]:
            rows.append(
                "<tr>"
                + (f"<td rowspan='{len(e['findings'])}' class='idc'><b>{esc(e['id'])}</b><br>"
                   f"<span class='gn'>{esc(e['global_name'][:70])}</span><br><span class='pg'>p.{e['page']}</span></td>" if first else "")
                + f"<td>{esc(f['kind'])}</td><td class='frd'>{esc(f['frd'])}</td>"
                + f"<td>{esc(f['expected'])}</td><td>{esc(f['fix'])}</td></tr>")
            first = False
    ok_items = "".join(f"<span class='okchip'>{esc(e['id'])} {esc(e['global_name'][:36])}</span>" for e in ok)
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<title>{esc(title)} — 디자인 시스템 정합 검사</title><style>
body{{font-family:'Samsung One','Malgun Gothic','Segoe UI',sans-serif;margin:0;background:#fff;color:#1c1c1c}}
.wrap{{max-width:1180px;margin:0 auto;padding:36px 24px}}
h1{{font-size:24px;margin:0 0 4px}}
.sub{{color:#767676;font-size:13.5px;margin-bottom:22px;line-height:1.7}}
.verdict{{font-size:18px;padding:16px 20px;border-radius:10px;margin-bottom:24px;font-weight:600}}
.verdict.bad{{background:#FDECEA;color:#C62828;border-left:5px solid #C62828}}
.verdict.good{{background:#E8F5E9;color:#2E7D32;border-left:5px solid #2E7D32}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}
th{{background:#1c1c1c;color:#fff;text-align:left;padding:10px 12px;white-space:nowrap}}
td{{padding:11px 12px;border-bottom:1px solid #eee;vertical-align:top;line-height:1.55}}
td.idc{{background:#FAFAFA;border-right:1px solid #eee;min-width:170px}}
.gn{{color:#555;font-size:12.5px}} .pg{{color:#999;font-size:11.5px}}
td.frd{{font-family:Consolas,monospace;color:#C62828;font-weight:600;white-space:nowrap}}
details{{margin-top:28px}} summary{{cursor:pointer;font-weight:600;font-size:14px;color:#2E7D32}}
.okchip{{display:inline-block;background:#F1F8E9;color:#33691E;border-radius:6px;padding:4px 10px;margin:3px;font-size:12px}}
footer{{color:#aaa;font-size:12px;margin-top:32px}}
@media print{{details{{display:none}}}}
</style></head><body><div class="wrap">
<h1>{esc(title)} — 디자인 시스템 정합 검사</h1>
<div class="sub">검사일 {meta['date']} · 기준 design-tokens v1.6 · 검사 항목: Field Description의 <b>색상 / 폰트 / 그림자</b> ↔ 승인 토큰 대조<br>
문서에서 요소 {meta['n_elements']}개 추출(검사값 보유 {meta['n_checked']}개), 커버리지: 정책 테이블이 텍스트로 추출되는 요소</div>
<div class="verdict {'bad' if bad else 'good'}">{'❌ 불일치 ' + str(len(bad)) + '개 요소 / ' + str(sum(len(e['findings']) for e in bad)) + '건' if bad else '✅ 검사한 모든 요소가 디자인 시스템과 일치'} &nbsp;·&nbsp; ✅ 일치 {len(ok)}개 요소</div>
<table><thead><tr><th>ID · Global Name</th><th>항목</th><th>FRD 명세값</th><th>디자인 시스템 기준</th><th>수정안</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<details><summary>✅ 일치 확인된 요소 {len(ok)}개 펼치기</summary><div style="margin-top:10px">{ok_items}</div></details>
<footer>FRD-QA · frd_ds_check — 명확한 값 불일치만 보고합니다 (상태·경계값·접근성 등 전체 감사는 별도 리포트)</footer>
</div></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--title", default=None)
    args = ap.parse_args()
    title = args.title or args.pdf.stem

    tk = load_tokens()
    elements, n_pages = extract_elements(args.pdf)

    bad, ok = [], []
    for el in elements:
        f = check_element(el, tk)
        has_values = bool(HEX_RE.search(el["desc"]) or FONT_RE.search(el["desc"]) or SHADOW_RE.search(el["desc"]))
        if f:
            bad.append({**el, "findings": f})
        elif has_values:
            ok.append(el)

    meta = {"date": date.today().isoformat(), "n_pages": n_pages,
            "n_elements": len(elements), "n_checked": len(bad) + len(ok)}
    out_html = REPO / "reports" / f"{args.pdf.stem}_DS-Conformance.html"
    out_json = REPO / "reports" / "data" / f"{args.pdf.stem}_ds-conformance.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"meta": meta, "mismatch": bad, "match": ok},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
    out_html.write_text(render_html(title, meta, bad, ok), encoding="utf-8")
    print(f"elements={meta['n_elements']} checked={meta['n_checked']} mismatch={len(bad)} match={len(ok)}")
    print(f"wrote {out_html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
