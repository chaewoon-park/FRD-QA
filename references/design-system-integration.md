# Design System 연동 가이드 (frd-ux-qa 스킬 references)

FRD UX/UI QA가 디자인 시스템을 판정 기준으로 사용하는 방법을 정의한다.
**모든 시각 판정(색상·타이포·간격·그리드)은 이 문서가 가리키는 데이터 파일을 단일 기준으로 삼는다.**

## 1. 기준 데이터 파일 (Single Source of Truth)

| 파일 | 내용 | 생성 방법 | 용도 |
|---|---|---|---|
| `src/frdqa/data/design-system-v1.6.json` | 카탈로그: 파운데이션 9종 규칙 + 엘리먼트 28종 분류(정의·타입·검토차원·**PDF 페이지 출처**) | PDF 문서에서 수작업 정리 | 컴포넌트 분류 판정, 검토 차원 결정, 리포트의 근거 페이지 인용 |
| `src/frdqa/data/design-tokens-v1.6.json` | 정밀 토큰: 색상 43, 타이포 51, 이펙트 3, 그리드 4 (**Figma 노드 출처** 포함) | `tools/extract_fig_tokens.py`로 .fig에서 자동 추출 | 값 대조 판정(hex, px, 행간, 그리드 컬럼/거터) |
| `src/frdqa/data/design-components-v1.6.json` | 컴포넌트 경로 1,923개 (SYMBOL 인덱스) | 〃 | FRD의 컴포넌트 명칭이 실제 라이브러리에 존재하는지 대조 |

두 소스는 상호 보완 관계다: **카탈로그 = 분류와 사용 규칙(왜)**, **토큰 = 정확한 값(무엇)**.
교차검증은 `frd-qa tokens-check`가 수행한다 (버전 일치, 카탈로그 색상/폰트 규칙이 토큰에 존재하는지, 행간 규칙 32↑=1.2 / 32↓=1.33 ±1px).

## 2. QA 판정 시 값 대조 규칙

- **색상**: FRD 스펙의 hex를 `tokens.colors`의 `$value`와 대소문자 무시 비교.
  일치하는 토큰이 없으면 `violation`(비승인 색상) — 단, FRD에 색상 명세 자체가 없으면 `insufficient_spec`.
  리포트 수정안에는 가장 가까운 승인 토큰명을 제시한다 (예: "`#2088FF` → 승인 토큰 `Primary color/Skyblue` `#2189FF`").
- **타이포**: 폰트 패밀리 비교 시 공백 제거·소문자 정규화 필수 (`Samsung One` ≡ `SamsungOne`).
  사이즈/행간은 `tokens.typography`의 플랫폼별(`pc`/`mobile`/`desktop`/`tablet`) 항목과 대조.
- **그리드/반응형**: `tokens.grids` 기준 — PC(1440) 12col/24 gutter, Mobile(360) 4col/16 gutter, 문서용 12col/28 gutter.
- **그림자**: `tokens.effects`의 Shadow 01/02 값(offset·radius·spread·alpha)과 수치 비교.
- **radius, z-index, 모션, 아이콘 크기**: 토큰에 없음 — **카탈로그 `foundations` rules를 기준으로 사용** (radius [4,6,8,20,24] 등).
- **컴포넌트 존재/명칭**: FRD가 언급한 컴포넌트가 카탈로그 `elements`의 id/types에 매칭되는지 우선 확인, 세부 변형은 `design-components` 경로에서 검색.

판정 불가 시 원칙: 토큰·카탈로그 어디에도 기준이 없으면 **추측 금지**, `insufficient_spec` 처리하고 검사 한계에 명시한다.

## 3. 근거 인용 형식

리포트의 모든 디자인 시스템 근거는 다음 형식으로 인용한다:

- 카탈로그 기반: `DesignSystem v1.6 p.82-86 (radius)`
- 토큰 기반: `design-tokens v1.6 "Primary color/Skyblue" (#2189FF, figma 1:xxxx)`

## 4. 버전 갱신 워크플로 (형상관리)

새 디자인 시스템 버전(예: v1.7)이 나오면:

1. 디자이너에게 **.fig 로컬 저장본** 수령 (Figma 링크 권한 불필요)
2. `python tools/extract_fig_tokens.py <새파일.fig> --version 1.7`
3. `git diff`로 토큰 변경분 리뷰 — diff가 곧 버전 간 변경 리포트
4. 카탈로그(`design-system-v1.7.json`)는 PDF Revision History를 참고해 수작업 갱신
5. `frd-qa tokens-check`로 교차검증 통과 확인 후 커밋

주의: .fig 디코더는 비공식 포맷(kiwi) 기반이므로 새 버전 수령 시마다 추출 성공 여부를 반드시 확인한다.
실패 시 폴백: PDF를 PyMuPDF로 렌더링해 시각 판독 (검증된 보조 경로).

## 5. 알려진 소스 결함

- `Global/Desktop/Title/Title 03 (400)`: 원본 .fig에 두 값(22px/행간30 vs 28px/행간38)으로 중복 정의.
  `tokens.conflicts[]`에 기록됨. 디자인팀 확인 전까지 이 스타일 관련 판정은 `insufficient_spec` 처리.
