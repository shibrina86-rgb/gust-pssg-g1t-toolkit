# 다음 Ayesha/유사 엔진 패치 작업 인계

## 처음 읽을 문서

1. [실행 파일 한글 패치 방법](ayesha-main-localization.md)
2. [내부 문자열 후보와 공통 영어 정책](ayesha-internal-strings.md)
3. 폰트가 대상이면 [폰트 작업](g1n-to-switch-font-workflow.md)
4. PSSG/G1T가 대상이면 [도움말 사례](a14-help-case-study.md)

## 현재 상태

- 마지막 사용자 정상 작동 확인본은 `main_ayesha_expanded_pc_6563_jpn_review`이다.
- 안전한 복구용으로 `main_ayesha_expanded_pc_4068_battle`을 별도 보관한다.
- 로컬 배포 패키지 이름은 `Ayesha_Korean_6563_test.zip`이다. 이름에 test가 남아 있어도 이후 사용자가 정상 작동을 보고했다. 전수 화면 검사 완료로 해석하지 않는다.
- 일본판과 영문판의 공통 영어는 추가 패치에서 제외한다는 사용자 선호를 유지한다.
- 공통 영어 제외 후 남은 57개는 내부 레코드 후보였다. 추가 500개를 만들 수 있다는 전제로 시작하지 않는다.

## 로컬에서 찾아야 할 자료

개인 경로를 저장소에 기록하지 않는다. 기존 작업 폴더의 `outputs/`와 `work/`에서 다음 파일을 찾거나 사용자에게 자료 위치를 확인한다.

| 자료 | 용도 |
|---|---|
| `AYESHA_PROGRESS.json` | 최신 기준본과 사용자 실행 확인 상태 |
| `ayesha_6563_jpn_review_manifest.json` | 참조 변경, 풀 주소, 출력 해시 |
| `translation_map_6563_jpn_review.csv` | 적용 번역과 글리프 매핑 결과 |
| `remaining_scan_audit.csv` | 미반영 후보 분류 |
| `shared_english_filter_summary.json` | 1,006개 공통/57개 비공통 집계 |
| `remaining_excluding_shared_jpn_english.csv` | 마지막 57개 검토 자료 |
| `jpn_all_display_refs.csv`, `code_scope_audit.csv` | 테이블/코드 참조 분석 근거 |
| `build_jpn_expansion.py`, `scope_expansion.py`, `scope_code.py` | 이 빌드 전용 구현을 검토할 출발점 |

로컬 스크립트는 개인 경로·고정 주소·이 빌드에 맞춘 휴리스틱을 포함한다. 범용 도구로 간주하지 말고 입력 검증 및 레이아웃 검사를 먼저 보강한다. 저장소에 실행 파일·추출 CSV 전체·폰트·개인 로그를 복사하지 않는다.

## 새 세션의 실제 시작 순서

1. 기준본 SHA-256과 사용자 현재 게임 빌드를 확인한다.
2. 기존 번역을 유지할지, 새 빌드로 이식할지 구분한다.
3. 화면에서 남은 영어가 있다면 화면 문맥과 문자열 참조를 먼저 찾는다.
4. 공통 영어 제외를 적용하고 후보 수를 보고한다.
5. 표시용 근거가 확보된 후보만 작업하며, 기존 정상본을 덮어쓰지 않는다.
6. 정적 검증과 사용자 게임 확인을 분리해 기록한다.

이 문서와 저장소 `AGENTS.md`가 다음 작업에서 다시 읽을 수 있는 인계 기록이다. 자동으로 모든 새 대화에 전달되는 기억을 보장하지 않으므로, 다른 폴더에서 시작할 때는 저장소 링크나 이 문서를 작업 문맥에 제공한다.
