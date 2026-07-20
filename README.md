# FRD-QA

Samsung.com Design System v1.6(KR)을 기준으로 구현 범위와 QA 근거를 추적하는 경량 CLI입니다.
원본 PDF의 내용을 복제하지 않고, 섹션 위치와 검증 관점만 구조화합니다.

## 현재 범위

- Principle: UX 및 Writing 원칙
- Foundation: Z-index, Color, Typeface, Iconography, Radius, Dimmed, Shadow, Motion, States
- Element: Badge부터 Tooltip까지 28개 항목
- 자동 검사: 카탈로그 무결성, 범위 누락, QA 관점별 증빙 누락
- 수동 검사: 시각, 상태, 반응형, 접근성, 문구 기준

## 빠른 실행

외부 패키지가 필요하지 않습니다.

```powershell
python -m unittest discover -s tests -v
$env:PYTHONPATH = "src"
python -m frdqa catalog-check
python -m frdqa audit examples\sample-inventory.json --output reports\sample-report.md
```

실제 프로젝트를 점검할 때는 `examples/sample-inventory.json`을 복사하고 다음을 기록합니다.

- `scope`: 이번 릴리스에서 사용하는 Element ID
- `components`: 구현된 타입과 QA가 완료된 관점
- `evidence`: Storybook, 테스트 케이스, 디자인 리뷰 등의 근거

명령은 오류나 누락이 있으면 종료 코드 `1`, 통과하면 `0`을 반환합니다.

## 기준 문서

- 문서: `DesignSystem_v1.6_Document_KR (Copy).pdf`
- 버전/발행일: v1.6 / 2025-09-18
- 전체 분량: 620쪽
- 페이지 번호는 PDF 뷰어의 실제 페이지 번호를 기준으로 기록했습니다.

세부 수동 점검 절차는 [qa/checklist.md](qa/checklist.md), 구조화된 추적 정보는
[src/frdqa/data/design-system-v1.6.json](src/frdqa/data/design-system-v1.6.json)을 참고합니다.
