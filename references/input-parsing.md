# FRD 입력 파싱 가이드 (PDF / PPTX)

입력 형식별 파싱 경로. 목업 시각 검사는 두 형식 공통으로 **페이지/슬라이드를 이미지로 렌더링해서 눈으로 확인**한다 — 데이터 추출만으로는 목업을 검사할 수 없다.

## 공통 준비

- `PYTHONUTF8=1` 필수 (Windows 한글 로케일 cp949 인코딩 오류 방지)
- 콘솔 출력 시 `io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")`

## PDF (검증된 경로 — 2026-07-22)

도구: **PyMuPDF** (`pip install pymupdf`, import 이름은 `fitz`)

```python
import fitz
doc = fitz.open(path)
```

| 목적 | 방법 | 주의 |
|---|---|---|
| 텍스트/앵커 ID | `page.get_text()` / `get_text("dict")` (span 단위 사이즈·색상 포함) | Figma 산출 PDF는 폰트가 Type3 익명 → **폰트명은 텍스트 레이어에서 추출 불가**, 시각 판독으로 보완 |
| 정확한 색상 | `page.get_drawings()`의 `fill` (0~1 float → hex 변환) | 벡터 도형만. 비트맵 영역은 렌더링 후 픽셀 검사 |
| 목업 시각 검사 | `page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))` → PNG 저장 → Read로 판독 | 1.5배율이면 1920×1080 슬라이드 기준 판독 충분. 세부 확인 필요 시 2~3배율 |
| 섹션 탐색 | 페이지별 `get_text()[:300]` 헤드에 키워드 매칭 | TOC(`get_toc()`)가 비어있는 문서 많음 — 텍스트 탐색이 기본 |

**Claude Code 내장 PDF Read**: 100MB 이하 파일만 가능(초과 시 거부). 대용량은 PyMuPDF로 분할하거나 렌더링 경로 사용.

## PPTX

도구: **python-pptx** (구조적 추출 — 표·텍스트·색상·폰트를 객체로 직접 읽음)

- **PDF로 변환하지 말 것** — 구조화 이점(표 객체, 도형 속성, 그룹 계층)을 잃는다.
- **그룹 도형은 재귀 순회 필수**: `shape.shape_type == MSO_SHAPE_TYPE.GROUP`이면 `shape.shapes`를 재귀 — 목업 안 텍스트가 그룹에 숨어있다.
- 표: `shape.has_table` → `table.rows/columns` 전 셀 순회. 병합 셀 주의.
- 시각 검사용 렌더링: PowerPoint COM(로컬 오피스) 또는 LibreOffice headless로 슬라이드→PNG. 둘 다 없으면 PPTX를 PDF로 export한 사본을 렌더링 전용으로만 사용.

## Figma .fig 로컬 저장본 (디자인 시스템 원본용)

`tools/extract_fig_tokens.py` 사용 — kiwi 파서 벤더링(`tools/vendor/`), `pip install zstandard`만 필요.
`pip install fig2sketch`는 zstd C 빌드 실패로 사용 불가. 상세는 `design-system-integration.md` §4.

## 파싱 품질 게이트 체크리스트 (스킬 2.5단계)

- [ ] 앵커 ID 전수 확보 (텍스트 탐색 + 렌더링 이미지 육안 대조)
- [ ] 테이블 전 행·열 독취 (행 수를 세어 명세 개수와 대조)
- [ ] (PPTX) 그룹 재귀 순회 완료
- [ ] 목업을 렌더링 이미지로 실제 확인
- 보강 2회 후에도 미확보 → "파싱 한계"로 기록, 추측 금지
