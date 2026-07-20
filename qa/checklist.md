# Design System v1.6 QA 체크리스트

각 항목의 판정은 `PASS`, `FAIL`, `N/A` 중 하나로 기록하고, `N/A`에는 사유를 남깁니다.
페이지 표기는 `data/design-system-v1.6.json`의 범위를 사용합니다.

## 1. 범위와 추적성

- [ ] 릴리스에서 사용하는 모든 Element가 inventory의 `scope`에 포함되어 있다.
- [ ] 각 Element가 Design System v1.6의 정의와 올바른 Type에 매핑된다.
- [ ] 디자인, 구현, 테스트 결과를 확인할 수 있는 URL 또는 파일 경로가 `evidence`에 있다.
- [ ] 이전 버전에서 삭제된 Layout, GNB Menu, LNB 항목을 v1.6 요구사항으로 간주하지 않는다.

## 2. 공통 Foundation

- [ ] 계층 값은 Z-index 기준(p.34-35)을 따르고 임의의 과도한 값을 만들지 않는다.
- [ ] 색상은 정의된 팔레트와 의미를 따르며, 텍스트 명도 대비는 최소 4.5:1이다(p.36-45).
- [ ] PC/Mobile 글꼴, 크기, 행간과 bounding box를 각각 확인한다(p.46-52).
- [ ] 아이콘은 동일 그룹에서 Stroke Type을 혼용하지 않고 정의된 크기를 사용한다(p.53-81).
- [ ] 컨테이너 Radius는 4/6/8/20/24px 체계 안에서 용도에 맞게 사용한다(p.82-86).
- [ ] Dimmed는 검정 60% 또는 90%를 의도에 맞게 사용한다(p.87-88).
- [ ] Shadow 01/02를 기준으로 하며 v1.6에서 삭제된 Shadow 03을 사용하지 않는다(p.89-90).
- [ ] Motion easing과 영역 크기별 200~500ms duration을 확인한다(p.91-99).
- [ ] 지원 상태의 시각적 차이와 상태 전환을 확인한다(p.100-110).

## 3. Element별 검증

### Definition / Type / Usage

- [ ] Element가 문서에 정의된 목적과 다른 기능으로 사용되지 않는다.
- [ ] 구현 Type이 카탈로그의 Type 중 하나이며, Type 선택 이유가 사용 맥락과 일치한다.
- [ ] Usage의 권장 사례와 금지 사례를 PC와 Mobile에서 각각 확인한다.

### Visual / State / Responsive

- [ ] 크기, 간격, 정렬, 색상, 타이포그래피, 아이콘이 디자인 원본과 일치한다.
- [ ] Normal, Hover, Pressed, Selected, Disabled 등 지원 상태를 키보드와 포인터로 확인한다.
- [ ] 입력 요소는 Resting, Typing, Error, Success와 보조 문구를 확인한다.
- [ ] 최소/최대 콘텐츠, 긴 번역, 빈 값, 200% 확대에서 잘림이나 겹침이 없다.
- [ ] PC와 Mobile 전환 시 정보·기능 손실이 없고 터치 영역이 충분하다.

### Accessibility / Writing

- [ ] 키보드만으로 접근, 실행, 종료할 수 있고 포커스 순서와 표시가 명확하다.
- [ ] 이름, 역할, 값과 상태 변화가 보조기술에 전달된다.
- [ ] 색상만으로 상태나 의미를 전달하지 않는다.
- [ ] 버튼, 링크, 입력 레이블이 다음 행동과 결과를 구체적으로 설명한다.
- [ ] 문구는 Actionability, Clarity, Consistency, Salience of Information 원칙을 따른다.

## 4. 릴리스 판정

- [ ] `python -m frdqa catalog-check`가 PASS이다.
- [ ] 대상 inventory의 `audit`가 오류 없이 PASS이다.
- [ ] 모든 FAIL에 결함 ID와 담당자, 목표 수정 버전이 연결되어 있다.
- [ ] N/A 판정과 예외 사용은 디자인 시스템 담당자의 승인 근거가 있다.

