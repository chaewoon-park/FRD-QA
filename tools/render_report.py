"""QA 리포트 JSON → 자체완결 HTML 렌더러.

Usage:
    python tools/render_report.py reports/data/<report>.json

출력: 같은 이름의 .html을 reports/ 에 생성.
외부 의존성 없는 단일 HTML (인라인 CSS/JS) — 더블클릭으로 브라우저에서 열림.
심각도/신뢰도 필터, 인쇄 친화 스타일 포함.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

SEV_COLOR = {"Blocker": "#D32F2F", "Major": "#EF6C00", "Minor": "#F9A825", "Info": "#607D8B"}
CONF_LABEL = {"violation": "확인", "insufficient_spec": "명세부족", "needs_code_check": "구현확인필요"}

CSS = """
*{box-sizing:border-box}
body{font-family:'Samsung One','Malgun Gothic','Segoe UI',sans-serif;margin:0;background:#F7F7F7;color:#1c1c1c}
.wrap{max-width:1280px;margin:0 auto;padding:32px 24px 64px}
header{background:#000;color:#fff;padding:28px 24px;border-radius:12px;margin-bottom:24px}
header h1{margin:0 0 6px;font-size:26px}
header .meta{color:#bbb;font-size:13px;line-height:1.7}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}
.card{flex:1;min-width:130px;background:#fff;border-radius:10px;padding:16px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.card .n{font-size:30px;font-weight:700}
.card .l{font-size:12px;color:#767676;margin-top:2px}
.risk{background:#FFF3E0;border-left:4px solid #EF6C00;border-radius:8px;padding:14px 18px;margin:16px 0}
.risk h3{margin:0 0 8px;font-size:15px}
.risk ol{margin:0;padding-left:20px;font-size:14px;line-height:1.8}
.filters{margin:20px 0 10px;display:flex;gap:8px;flex-wrap:wrap}
.filters button{border:1px solid #ddd;background:#fff;border-radius:20px;padding:6px 14px;font-size:13px;cursor:pointer}
.filters button.on{background:#000;color:#fff;border-color:#000}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);font-size:13.5px}
th{background:#1c1c1c;color:#fff;padding:10px 12px;text-align:left;font-weight:600;white-space:nowrap}
td{padding:12px;border-top:1px solid #eee;vertical-align:top;line-height:1.6}
tr:hover td{background:#FAFCFF}
.badge{display:inline-block;padding:2px 10px;border-radius:12px;color:#fff;font-size:12px;font-weight:700;white-space:nowrap}
.chip{display:inline-block;padding:2px 8px;border-radius:4px;background:#EEE;color:#555;font-size:11.5px;white-space:nowrap}
.rule{font-family:Consolas,monospace;font-size:12.5px;background:#F0F4FF;color:#1a4fba;padding:2px 6px;border-radius:4px;white-space:nowrap}
section{background:#fff;border-radius:10px;padding:20px 24px;margin:18px 0;box-shadow:0 1px 3px rgba(0,0,0,.08)}
section h2{font-size:17px;margin:0 0 12px;border-bottom:2px solid #000;padding-bottom:8px}
section ul{margin:0;padding-left:20px;font-size:14px;line-height:1.9}
.feedback{background:#F0F7FF;border:1px dashed #2189FF}
.feedback label{display:block;margin:10px 0 4px;font-size:13.5px;font-weight:600}
.feedback textarea{width:100%;min-height:44px;border:1px solid #cdd;border-radius:6px;padding:8px;font:inherit;font-size:13px}
footer{color:#999;font-size:12px;text-align:center;margin-top:28px}
@media print{.filters,.feedback textarea{display:none}body{background:#fff}section,table{box-shadow:none}}
"""

JS = """
function filt(kind, val, btn){
  document.querySelectorAll('.filters[data-kind='+kind+'] button').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  window.__f = window.__f || {sev:'all', conf:'all'};
  window.__f[kind==='sev'?'sev':'conf'] = val;
  document.querySelectorAll('#issues tbody tr').forEach(tr=>{
    const okS = window.__f.sev==='all' || tr.dataset.sev===window.__f.sev;
    const okC = window.__f.conf==='all' || tr.dataset.conf===window.__f.conf;
    tr.style.display = (okS&&okC)?'':'none';
  });
}
"""


def esc(s) -> str:
    return html.escape(str(s), quote=False)


def render(data: dict) -> str:
    meta = data["meta"]
    issues = data["issues"]
    sev_counts = {s: sum(1 for i in issues if i["severity"] == s) for s in ("Blocker", "Major", "Minor", "Info")}
    conf_counts = {c: sum(1 for i in issues if i["confidence"] == c) for c in CONF_LABEL}

    rows = []
    for i in issues:
        sev = i["severity"]
        conf = i["confidence"]
        rows.append(
            f"<tr data-sev='{sev}' data-conf='{conf}'>"
            f"<td>{i['no']}</td>"
            f"<td>{esc(i['target'])}</td>"
            f"<td><span class='rule'>{esc(i['rule'])}</span><br><span class='chip'>{esc(i['group'])}</span></td>"
            f"<td><span class='badge' style='background:{SEV_COLOR[sev]}'>{sev}</span></td>"
            f"<td><span class='chip'>{CONF_LABEL.get(conf, conf)}</span></td>"
            f"<td>{esc(i['problem'])}</td>"
            f"<td>{esc(i['evidence'])}</td>"
            f"<td>{esc(i['fix'])}</td></tr>"
        )

    def ul(items):
        return "".join(f"<li>{esc(x)}</li>" for x in items)

    cards = "".join(
        f"<div class='card'><div class='n' style='color:{SEV_COLOR[s]}'>{n}</div><div class='l'>{s}</div></div>"
        for s, n in sev_counts.items()
    )
    conf_line = " · ".join(f"{CONF_LABEL[c]} {n}" for c, n in conf_counts.items() if n)

    sev_btns = "<button class='on' onclick=\"filt('sev','all',this)\">전체</button>" + "".join(
        f"<button onclick=\"filt('sev','{s}',this)\">{s} ({n})</button>" for s, n in sev_counts.items() if n
    )
    conf_btns = "<button class='on' onclick=\"filt('conf','all',this)\">전체</button>" + "".join(
        f"<button onclick=\"filt('conf','{c}',this)\">{CONF_LABEL[c]} ({n})</button>" for c, n in conf_counts.items() if n
    )

    feedback_fields = [
        "잘못 지적된 이슈(오탐) — 이슈 번호와 이유",
        "놓친 문제(미탐) — 무엇을, 어느 요소에서",
        "심각도가 부적절한 이슈 — 번호와 제안 등급",
        "규칙 자체 수정 제안 — 규칙 ID와 방향",
        "기타 코멘트",
    ]
    feedback = "".join(f"<label>{f}</label><textarea placeholder='작성 후 인쇄/저장하거나 내용을 회신해 주세요'></textarea>" for f in feedback_fields)

    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>UX/UI QA 리포트 — {esc(meta['title'])}</title>
<style>{CSS}</style><script>{JS}</script></head>
<body><div class="wrap">
<header>
  <h1>UX/UI QA 리포트 — {esc(meta['title'])}</h1>
  <div class="meta">
    검사일 {esc(meta['date'])} · {esc(meta['tool'])}<br>
    기준: {esc(meta['baseline'])}<br>
    입력: {esc(meta['input'])}<br>
    범위: {esc(meta['scope'])} · 규모: {esc(meta['document_scale'])}
  </div>
</header>

<div class="cards">{cards}
  <div class="card"><div class="n">{len(issues)}</div><div class="l">전체 이슈</div></div>
</div>
<div style="font-size:13px;color:#767676">신뢰도: {conf_line}</div>

<div class="risk"><h3>⚠ 최상위 리스크</h3><ol>{ul(data['top_risks'])}</ol></div>

<div class="filters" data-kind="sev">심각도&nbsp; {sev_btns}</div>
<div class="filters" data-kind="conf">신뢰도&nbsp; {conf_btns}</div>
<table id="issues">
<thead><tr><th>#</th><th>대상</th><th>규칙</th><th>심각도</th><th>신뢰도</th><th>문제</th><th>근거</th><th>수정안</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>

<section><h2>그룹별 관찰</h2><ul>{ul(data['observations'])}</ul></section>
<section><h2>검사 한계</h2><ul>{ul(data['limitations'])}</ul></section>
<section><h2>규칙 개선 후보 (순환 2 입력)</h2><ul>{ul(data['proposals'])}</ul></section>
<section class="feedback"><h2>피드백 수집 (검토자 작성란)</h2>{feedback}</section>

<footer>FRD-QA · 이 리포트는 도구가 생성했으며 모든 판정에 규칙 ID와 근거가 있습니다 · 피드백은 다음 검사 개선의 입력이 됩니다</footer>
</div></body></html>"""


def main() -> int:
    src = Path(sys.argv[1])
    data = json.loads(src.read_text(encoding="utf-8"))
    out = src.parents[1] / (src.stem + "_QA.html")
    out.write_text(render(data), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
