# Gust PSSG/G1T Toolkit

거스트 계열 게임의 PSSG 내부 G1T 이식과 Switch용 개별 G1T 재구축을 안전하게 반복하기 위한 작은 도구와 실전 기록입니다.

이 저장소에는 게임 원본, 번역 이미지, 폰트, 실행 파일이 없습니다. 사용자가 합법적으로 보유한 파일을 직접 준비해야 합니다.

## 가장 중요한 원칙

1. **PSSG 안에 실제로 존재하는 같은 이름의 G1T만 교체합니다.**
2. PC와 Switch G1T의 전체 크기, 헤더 크기, 텍스처 수가 같을 때만 이식합니다.
3. Switch 결과의 플랫폼 필드는 `0x10`으로 되돌립니다.
4. 대상 G1T가 원본에서 별도 폴더에 있었다면 PSSG에 추가하지 말고 같은 상대 경로의 개별 파일로 배치합니다.
5. 자체 파서로 다시 읽힌다는 사실만으로 게임 호환성을 판단하지 않습니다. 객체 목록과 원본 로딩 경로까지 보존해야 합니다.

## 설치

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## PSSG 내부 G1T 확인 및 이식

먼저 두 PSSG가 같은 리소스 집합인지 확인합니다.

```powershell
python tools/pssg_g1t_transplant.py inspect switch_original.PSSG
python tools/pssg_g1t_transplant.py inspect pc_patched.PSSG
```

이름과 구조가 모두 대응될 때만 이식합니다.

```powershell
python tools/pssg_g1t_transplant.py transplant `
  switch_original.PSSG pc_patched.PSSG output_switch.PSSG
```

결과 PSSG의 크기와 리소스 순서는 Switch 원본과 같아야 합니다.

## 개별 BC1 G1T 편집

```powershell
python tools/g1t_bc1.py extract original_g1t extracted_png --glob "*.g1t"
```

PNG를 편집하되 해상도를 바꾸지 않은 뒤 다시 만듭니다.

```powershell
python tools/g1t_bc1.py rebuild original_g1t edited_png rebuilt_g1t `
  --glob "*.g1t.png" --platform 0x10
```

## PSSG에 넣을지, 개별 G1T로 둘지 판단하기

```text
Switch 원본 PSSG에 같은 리소스 이름이 있는가?
├─ 예 → 동일 크기·동일 구조일 때만 in-place transplant
└─ 아니오
   └─ Switch 원본의 인접 폴더에 개별 G1T가 있는가?
      ├─ 예 → 원래 상대 경로에 개별 G1T로 배치
      └─ 아니오 → 정확한 컨테이너/참조를 더 조사하고 수정 중단
```

A14 도움말에서 실제로 발생한 실패와 해결 과정은 [사례 기록](docs/a14-help-case-study.md)에 정리했습니다.

## 제한 사항

- `g1t_bc1.py`는 현재 고정 헤더 형식의 단일 BC1 텍스처를 대상으로 합니다.
- `pssg_g1t_transplant.py`는 리소스 이름이 G1T 블록 앞 160바이트 안에 있는 BINARYOBJECT 계열 PSSG를 대상으로 합니다.
- ASTC, BC3/BC7, 스위즐된 텍스처, 여러 밉맵은 별도 처리가 필요할 수 있습니다.
- 원본 백업과 실제 기기/에뮬레이터 검증은 필수입니다.

## 나중에 Codex/AI가 참고할 체크리스트

- 원본과 출력의 파일 크기 및 SHA-256 기록
- PSSG 리소스 이름·순서·개수 비교
- G1T `GT1G` 매직, 선언 크기, 플랫폼 값 확인
- 편집 후 해상도와 압축 데이터 길이 불변 확인
- PSSG에 없던 객체를 임의 추가하지 않기
- 실제 로딩 경로를 먼저 확인하고, 성공한 최소 변경을 기준본으로 유지


