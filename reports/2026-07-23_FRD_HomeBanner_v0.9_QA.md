# UX/UI QA 리포트 — FRD_HomeBanner v0.9

- 검사 일시: 2026-07-23 · 검사 도구: frd-ux-qa (master-rules 44개 규칙)
- 기준 데이터: design-system v1.6 카탈로그 + design-tokens v1.6 (.fig 추출)
- 입력: `FRD_HomeBanner_v0.9.pptx` (3슬라이드 — 표지/개정이력/D. Home Banner)

## 요약

- 검사 요소 수: **5** (D1.0, D2.0, D4.0, D5.0, D6.0) + 문서 레벨 / 발견 이슈 수: **20**
- 심각도별 집계: **Blocker 1 · Major 16 · Minor 3 · Info 0**
- 신뢰도별 집계: 확인(violation) 19 · 명세부족 0 · 구현확인필요 1
- 디자인 시스템 적용 여부: **적용** (v1.6 토큰·카탈로그 대조)
- 최상위 리스크 3가지:
  1. D5.0 추천 상품 리스트에 empty/loading/error 상태가 전혀 없음 — 구현 착수 불가 (Blocker)
  2. D2.0 CTA의 핵심 동작(on_action)이 TBD — 배너의 존재 이유가 미정
  3. 접근성 대비 미달 2건 (CTA 3.48:1, 법적 고지 3.23:1) — WCAG 2.2 위반 확정

## 이슈 목록

| # | 대상 | 규칙 | 심각도 | 신뢰도 | 문제 | 근거 | 수정안 |
|---|---|---|---|---|---|---|---|
| 1 | D5.0 · Home Banner · PC/Mobile | ST-02 (상태) | **Blocker** | violation | 리스트의 empty/loading/error 상태 미정의 | NN/g #1 시스템 상태 가시성 | 3상태 각각의 UI·문구 정의 추가 (empty: "추천 상품 준비 중" + 대체 콘텐츠, error: 재시도 버튼) |
| 2 | D2.0 · Home Banner · PC/Mobile | IX-02 (인터랙션) | Major | violation | On action = "TBD" — 클릭 결과 미정 | 흐름 완결성 | 목적지 URL/화면 ID 특정 (예: 사전판매 상품 상세 `/event/preorder`) |
| 3 | D2.0 · Home Banner · PC/Mobile | DS-01 (DS값) | Major | violation | CTA 배경 #2088FF는 비승인 색 | design-tokens v1.6 colors | 승인 토큰 `Primary color/Skyblue` **#2189FF**로 교체 |
| 4 | D2.0 · Home Banner · PC/Mobile | DS-02 (DS값) | Major | violation | SamsungOne 700 15px/20은 승인 타입스케일에 없음 | design-tokens v1.6 typography | `Body 03 (700)` 16px/22 또는 `Body 04 (700)` 14px/19로 교체 |
| 5 | D2.0 · Home Banner · PC/Mobile | AC-01 (접근성) | Major | violation | FG #FFFFFF / BG #2088FF 대비 **3.48:1** < 4.5:1 (15px는 소형 텍스트) | WCAG 2.2 1.4.3 | 텍스트 18pt↑ 확대 또는 배경 어두운 톤 조정. ※승인 Skyblue(#2189FF)도 백색 텍스트와 ~3.4:1 — 규칙 개선 후보 #3 참조 |
| 6 | D2.0 · Home Banner · PC/Mobile | CB-01 (경계값) | Major | violation | Max chars 공란 — CTA 문구 길이 한도 없음 | 콘텐츠 설계 규약 | 최대 글자수 정의 (권장: KR 8자, 초과 시 금지 규정) |
| 7 | D2.0 · Home Banner · PC/Mobile | ST-01 (상태) | Major | violation | hover만 정의 — pressed/disabled 미명세 | DesignSystem v1.6 p.100-110 | baseline 상태별 스펙 추가 (pressed: BG 20% 어둡게, disabled: Grayscale 토큰) |
| 8 | D2.0 · Home Banner · Mobile | RS-03 (반응형) | Major | violation | hover 스펙만 존재 — Mobile 대체 인터랙션 없음 | 모바일 UX 원칙 | Mobile은 pressed 상태로 치환 명시 |
| 9 | D2.0 · Home Banner · Mobile | AC-03 (접근성) | Major | violation | 터치 타깃 크기 미명세 | WCAG 2.2 2.5.8 | 최소 44×44px 명세 추가 |
| 10 | D3.0 · Home Banner · PC/Mobile | CN-01 (정합성) | Major | violation | 목업 앵커 D3.0(서브카피 위치)에 대응하는 정책 테이블 행 없음 | 스킬 구조화 규약 | D3.0 행 추가 또는 앵커 제거 (D6.0=Sub Copy와의 관계 정리 — 이슈 #19 참조) |
| 11 | D4.0 · Home Banner · PC | CN-01 (정합성) | Major | violation | 테이블 행 D4.0(Legal Text)의 목업 앵커 없음 | 〃 | 목업에 D4.0 앵커 표기 |
| 12 | D5.0 · Home Banner · PC/Mobile | CN-01 (정합성) | Major | violation | 테이블 행 D5.0(추천 상품 리스트)이 목업에 미표현 | 〃 | 리스트 목업 + 앵커 추가 |
| 13 | D4.0 · Home Banner · PC | AC-01 (접근성) | Major | violation | #8F8F8F on #FFFFFF 대비 **3.23:1** < 4.5:1 (12px 소형 텍스트) | WCAG 2.2 1.4.3, DesignSystem p.36-45 | `Grayscale/7_55` **#555555** (대비 7.46:1)로 교체 |
| 14 | D1.0 · Home Banner · PC/Mobile | AC-02 (접근성) | Major | violation | 배너 이미지 대체 텍스트 정책 미명세 | WCAG 2.2 1.1.1 | alt 작성 규칙 추가 (캠페인명+핵심 혜택) |
| 15 | D1.0 · Home Banner · PC/Mobile | RS-01 (반응형) | Major | violation | PC/Mobile 선언인데 플랫폼별 배너 규격(비율/크기) 미분리 | 스킬 구조화 규약 | PC(12col 기준 px)·Mobile(360 기준) 각 규격 명시 |
| 16 | D5.0 · Home Banner · PC/Mobile | CB-01 (경계값) | Major | violation | 카드 내 상품명/가격의 길이·말줄임 정책 없음 ("-" 처리) | 콘텐츠 설계 규약 | 상품명 2줄 ellipsis 등 정책 추가 |
| 17 | D5.0 · Home Banner · PC/Mobile | CB-05 (경계값) | Major | violation | 상품 0개/1개/최대 개수 케이스 미정의 | 경계값 분석 | 최소·최대 카드 수, 0개 시 영역 처리 정의 (#1과 연계) |
| 18 | 문서 · 표지/개정이력 | CN-03 (정합성) | Minor | violation | 표지 v0.9 ↔ 개정이력 최신 v1.0 불일치 | 문서 관리 규약 | 표지 버전을 v1.0으로 갱신 |
| 19 | D6.0 · Home Banner · PC/Mobile | VI-03 (시각검증) | Minor | violation | 목업의 D6.0 앵커가 법적 고지 옆에 위치하나 테이블 D6.0은 Sub Copy — 앵커 오지정 | 렌더링 이미지 판독 | D6.0 앵커를 서브카피 옆으로 이동(또는 D4.0/D6.0 라벨 교차 수정) |
| 20 | D2.0 · Home Banner · PC | AC-04 (접근성) | Minor | needs_code_check | 키보드 포커스 표시자 정책 미명세 — 구현 여부는 코드 확인 필요 | WCAG 2.2 2.4.7 | 포커스 아웃라인 정책 1줄 추가 |

## 그룹별 관찰

- **상태 완결성**: 인터랙티브 요소 2개(D2.0, D5.0) 모두 상태 정의 불충분. 상태 정의가 문서 전반에서 누락되는 패턴.
- **인터랙션**: 핵심 CTA의 목적지가 TBD인 것이 문서의 가장 큰 공백. D5.0의 Swipe는 목적지는 명확하나 PC 조작 수단 미정(규칙 개선 후보 #1).
- **콘텐츠 경계값**: D6.0만 모범적(30자 한도 명시). 나머지 텍스트 요소는 길이 정책 부재.
- **반응형**: "PC, Mobile" 선언은 있으나 실질 스펙 분리는 D none — 선언과 명세의 괴리가 반복됨.
- **접근성**: 대비 위반 2건 모두 스펙 hex로 결정적 판정 가능했음. 명세 자체가 없는 항목(alt, 터치타깃, 포커스)이 더 많음.
- **흐름**: 이 FRD는 단일 섹션 명세라 화면 간 흐름(FL 그룹) 판정 대상 아님 — 검사 한계 참조.
- **디자인 시스템 정합**: 통과 사례도 확인됨 — D1.0 radius 8·배경 #EEEEEE(Grayscale/1_EE), D6.0 #555555·14px/19 모두 승인 토큰과 일치.

## 검사 한계

- FL 그룹(흐름 4개 규칙): 단일 섹션 FRD로 화면 전이 정보가 없어 판정 불가 — 전체 화면 흐름 FRD에서 재검 필요.
- AC-04(포커스), 모션 관련 구현 품질: 명세 누락만 잡을 수 있고 실제 구현 위반은 코드/빌드 검증 필요.
- 목업이 개념도 수준(실디자인 아님)이라 VI-01/VI-02(시각 정밀 대조)는 앵커 위치(VI-03) 외 제한적으로만 적용.
- D5.0 캐러셀의 인디케이터/페이지네이션 스펙 부재 — 카탈로그 Indicator(p.273-295) 기준 상세 검사는 스펙 보강 후 가능.

## 규칙 개선 후보 (순환 2 입력)

1. **[신규 제안] RS-05 제스처 상호 치환**: Mobile 제스처(Swipe)가 PC에 선언될 때 마우스/키보드 대체 수단(화살표 버튼 등) 요구 — D5.0 사례. 현행 RS-03은 hover→Mobile 방향만 커버.
2. **[보강 제안] DS-01**: "BG 10% 어둡게" 같은 파생 색 표현 허용 여부 — 토큰 참조 강제 또는 파생 규칙 정의 필요 (D2.0 hover 사례).
3. **[디자인 시스템 이슈] AC-01×DS-01 충돌**: 승인 조합인 White on Skyblue(#2189FF)도 대비 ~3.4:1로 소형 텍스트 기준 미달. 디자인 시스템 차원의 검토 필요 — 토큰이 규칙을 이길 수 없음.

## 피드백 수집 (검토자 작성란)

> 이 리포트를 검토한 사람이 직접 채운다. 다음 검사 개선의 입력이 된다.
- [ ] 잘못 지적된 이슈(오탐) — 이슈 번호와 이유:
- [ ] 놓친 문제(미탐) — 무엇을, 어느 요소에서:
- [ ] 심각도가 부적절한 이슈 — 번호와 제안 등급:
- [ ] 규칙 자체 수정 제안 — 규칙 ID와 방향:
- [ ] 기타 코멘트:
