from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CATALOG = Path(__file__).resolve().parent / "data" / "design-system-v1.6.json"
DEFAULT_TOKENS = Path(__file__).resolve().parent / "data" / "design-tokens-v1.6.json"


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    subject: str
    message: str


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except FileNotFoundError as exc:
        raise ValueError(f"파일을 찾을 수 없습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 형식 오류: {path}:{exc.lineno}:{exc.colno}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"최상위 JSON 값은 객체여야 합니다: {path}")
    return value


def check_catalog(catalog: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    document = catalog.get("document", {})
    page_count = document.get("page_count")
    if document.get("version") != "1.6":
        findings.append(Finding("error", "CATALOG_VERSION", "document", "버전은 1.6이어야 합니다."))
    if not isinstance(page_count, int) or page_count < 1:
        findings.append(Finding("error", "PAGE_COUNT", "document", "유효한 전체 페이지 수가 필요합니다."))
        page_count = 0

    for group, expected in (("foundations", 9), ("elements", 28)):
        items = catalog.get(group)
        if not isinstance(items, list):
            findings.append(Finding("error", "GROUP_MISSING", group, "목록이 필요합니다."))
            continue
        if len(items) != expected:
            findings.append(Finding("error", "GROUP_COUNT", group, f"{expected}개가 필요하지만 {len(items)}개입니다."))
        seen: set[str] = set()
        for item in items:
            item_id = item.get("id", "<unknown>") if isinstance(item, dict) else "<invalid>"
            if not isinstance(item, dict):
                findings.append(Finding("error", "ITEM_TYPE", group, "항목은 객체여야 합니다."))
                continue
            if not item.get("id") or not item.get("name"):
                findings.append(Finding("error", "ITEM_IDENTITY", item_id, "id와 name이 필요합니다."))
            if item_id in seen:
                findings.append(Finding("error", "DUPLICATE_ID", item_id, "중복 ID입니다."))
            seen.add(item_id)
            pages = item.get("pages")
            if (
                not isinstance(pages, list)
                or len(pages) != 2
                or not all(isinstance(n, int) for n in pages)
                or pages[0] > pages[1]
                or pages[0] < 1
                or pages[1] > page_count
            ):
                findings.append(Finding("error", "PAGE_RANGE", item_id, "페이지 범위가 잘못되었습니다."))
            if group == "elements":
                for field in ("definition", "types", "review_dimensions"):
                    if not item.get(field):
                        findings.append(Finding("error", "ELEMENT_FIELD", item_id, f"{field} 값이 필요합니다."))
    return findings


def _normalize_family(name: str) -> str:
    return "".join(str(name).lower().split())


def check_tokens(catalog: dict[str, Any], tokens: dict[str, Any]) -> list[Finding]:
    """토큰 파일 무결성 + 카탈로그(문서 규칙) 교차검증."""
    findings: list[Finding] = []
    meta = tokens.get("meta", {})

    # 1) 버전·출처 무결성
    if meta.get("design_system_version") != catalog.get("document", {}).get("version"):
        findings.append(Finding("error", "TOKENS_VERSION", "meta", "토큰 버전이 카탈로그와 다릅니다."))
    source = meta.get("source", {})
    if not source.get("sha256"):
        findings.append(Finding("error", "TOKENS_PROVENANCE", "meta", "소스 파일 sha256이 없습니다."))

    # 2) meta.counts와 실제 개수 일치
    counts = meta.get("counts", {})
    for group in ("colors", "typography", "effects", "grids"):
        actual = len(tokens.get(group, {}))
        if counts.get(group) != actual:
            findings.append(
                Finding("error", "TOKENS_COUNT", group, f"meta.counts={counts.get(group)} 실제={actual}")
            )

    # 3) 소스 충돌(동일 이름·다른 값) — 디자인 파일 자체 결함
    for conflict in tokens.get("conflicts", []):
        findings.append(
            Finding("warning", "SOURCE_CONFLICT", conflict.get("name", "?"), "원본 .fig에 중복 정의된 스타일입니다.")
        )

    foundations = {f["id"]: f for f in catalog.get("foundations", []) if isinstance(f, dict)}

    # 4) 색상 교차검증: 카탈로그 색상 규칙값이 토큰 팔레트에 존재해야 함
    token_hexes = {
        str(v.get("$value", "")).upper()
        for v in tokens.get("colors", {}).values()
        if isinstance(v, dict)
    }
    color_rules = foundations.get("color", {}).get("rules", {})
    for rule_name, rule_value in color_rules.items():
        if isinstance(rule_value, str) and rule_value.startswith("#"):
            if rule_value.upper() not in token_hexes:
                findings.append(
                    Finding("error", "COLOR_MISSING", rule_name, f"카탈로그 색상 {rule_value}이 토큰에 없습니다.")
                )

    # 5) 타이포 교차검증: 폰트 패밀리 + 행간 규칙(32 이상 1.2 / 미만 1.33, 반올림 ±1px)
    typeface_rules = foundations.get("typeface", {}).get("rules", {})
    token_families = {
        _normalize_family(f"{v.get('family', '')} {v.get('style', '')}")
        for v in tokens.get("typography", {}).values()
        if isinstance(v, dict)
    } | {
        _normalize_family(v.get("family", ""))
        for v in tokens.get("typography", {}).values()
        if isinstance(v, dict)
    }
    for rule_name in ("display-font", "body-font"):
        expected = typeface_rules.get(rule_name)
        if expected and _normalize_family(expected) not in token_families:
            findings.append(
                Finding("error", "TYPEFACE_MISSING", rule_name, f"카탈로그 폰트 '{expected}'이 토큰에 없습니다.")
            )
    for name, token in tokens.get("typography", {}).items():
        if not isinstance(token, dict):
            continue
        size = token.get("size")
        line_height = (token.get("lineHeight") or {}).get("value")
        units = (token.get("lineHeight") or {}).get("units")
        if not isinstance(size, (int, float)) or not isinstance(line_height, (int, float)) or units != "PIXELS":
            continue
        ratio = 1.2 if size >= 32 else 1.33
        if abs(line_height - size * ratio) > 1:
            findings.append(
                Finding(
                    "warning",
                    "LINE_HEIGHT_RULE",
                    name,
                    f"행간 {line_height}px가 규칙({size}×{ratio}={size * ratio:.1f}±1)을 벗어납니다.",
                )
            )
    return findings


def audit(catalog: dict[str, Any], inventory: dict[str, Any]) -> list[Finding]:
    findings = check_catalog(catalog)
    if any(f.level == "error" for f in findings):
        return findings
    if inventory.get("design_system_version") != catalog["document"]["version"]:
        findings.append(Finding("error", "VERSION_MISMATCH", "inventory", "디자인 시스템 버전이 카탈로그와 다릅니다."))

    catalog_items = {item["id"]: item for item in catalog["elements"]}
    scope = inventory.get("scope")
    records = inventory.get("components")
    if not isinstance(scope, list) or not scope:
        findings.append(Finding("error", "SCOPE_EMPTY", "inventory", "하나 이상의 scope가 필요합니다."))
        return findings
    if len(scope) != len(set(scope)):
        findings.append(Finding("error", "SCOPE_DUPLICATE", "inventory", "scope에 중복 ID가 있습니다."))
    if not isinstance(records, list):
        findings.append(Finding("error", "COMPONENTS_MISSING", "inventory", "components 목록이 필요합니다."))
        return findings

    for item_id in sorted(set(scope) - set(catalog_items)):
        findings.append(Finding("error", "UNKNOWN_COMPONENT", item_id, "카탈로그에 없는 Element입니다."))

    record_map: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not record.get("id"):
            findings.append(Finding("error", "INVALID_RECORD", "components", "각 항목에 id가 필요합니다."))
            continue
        item_id = record["id"]
        if item_id in record_map:
            findings.append(Finding("error", "DUPLICATE_RECORD", item_id, "구현 기록이 중복되었습니다."))
        record_map[item_id] = record

    for item_id in scope:
        if item_id not in catalog_items:
            continue
        if item_id not in record_map:
            findings.append(Finding("error", "MISSING_IMPLEMENTATION", item_id, "범위에 포함됐지만 구현 기록이 없습니다."))
            continue
        record = record_map[item_id]
        allowed_types = set(catalog_items[item_id]["types"])
        implemented_types = record.get("implemented_types", [])
        if not isinstance(implemented_types, list) or not implemented_types:
            findings.append(Finding("error", "TYPE_EMPTY", item_id, "하나 이상의 구현 Type이 필요합니다."))
        else:
            for type_name in sorted(set(implemented_types) - allowed_types):
                findings.append(Finding("error", "UNKNOWN_TYPE", item_id, f"카탈로그에 없는 Type입니다: {type_name}"))
        expected = set(catalog_items[item_id]["review_dimensions"])
        completed = set(record.get("reviewed", []))
        for dimension in sorted(expected - completed):
            findings.append(Finding("error", "REVIEW_MISSING", item_id, f"'{dimension}' 검토 근거가 없습니다."))
        for dimension in sorted(completed - expected):
            findings.append(Finding("warning", "UNKNOWN_REVIEW", item_id, f"카탈로그에 없는 검토 관점입니다: {dimension}"))
        evidence = record.get("evidence", [])
        if not isinstance(evidence, list) or not any(str(value).strip() for value in evidence):
            findings.append(Finding("error", "EVIDENCE_EMPTY", item_id, "최소 하나의 검증 근거가 필요합니다."))

    for item_id in sorted(set(record_map) - set(scope)):
        findings.append(Finding("warning", "OUT_OF_SCOPE_RECORD", item_id, "scope 밖의 구현 기록입니다."))
    return findings


def render_report(title: str, findings: list[Finding]) -> str:
    errors = sum(item.level == "error" for item in findings)
    warnings = sum(item.level == "warning" for item in findings)
    status = "PASS" if errors == 0 else "FAIL"
    lines = [f"# {title}", "", f"- 결과: **{status}**", f"- 오류: {errors}", f"- 경고: {warnings}", ""]
    if findings:
        lines.extend(["## 발견 사항", "", "| 수준 | 코드 | 대상 | 내용 |", "|---|---|---|---|"])
        for item in findings:
            message = item.message.replace("|", "\\|")
            lines.append(f"| {item.level} | `{item.code}` | `{item.subject}` | {message} |")
    else:
        lines.append("발견된 문제가 없습니다.")
    return "\n".join(lines) + "\n"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="frd-qa", description="Design System v1.6 QA 추적 도구")
    result.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("catalog-check", help="카탈로그 무결성을 검사합니다.")
    tokens_parser = commands.add_parser("tokens-check", help="토큰 무결성과 카탈로그 교차검증을 수행합니다.")
    tokens_parser.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS)
    tokens_parser.add_argument("--output", type=Path)
    audit_parser = commands.add_parser("audit", help="구현 인벤토리의 QA 누락을 검사합니다.")
    audit_parser.add_argument("inventory", type=Path)
    audit_parser.add_argument("--output", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        catalog = load_json(args.catalog)
        if args.command == "catalog-check":
            findings = check_catalog(catalog)
            title = "Design System 카탈로그 검사"
        elif args.command == "tokens-check":
            findings = check_tokens(catalog, load_json(args.tokens))
            title = "Design System 토큰 검사"
        else:
            findings = audit(catalog, load_json(args.inventory))
            title = f"FRD-QA 감사 보고서: {args.inventory.name}"
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    report = render_report(title, findings)
    output = getattr(args, "output", None)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        print(output)
    else:
        print(report, end="")
    return 1 if any(item.level == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
