# PC G1N에서 Switch OTF/TTF를 준비한 작업 기록

## 핵심 구분

G1N은 Koei Tecmo/Gust 게임에서 쓰이는 비트맵 폰트 컨테이너입니다. OTF/TTF와 같은 벡터 폰트가 아니므로 G1N을 단순히 확장자만 바꿔 OTF로 만들 수는 없습니다.

이번에 정상 동작한 방식은 다음 세 단계를 조합한 것입니다.

1. PC 패치 G1N 또는 그것을 읽을 수 있게 변환한 글꼴에서 **문자 코드 슬롯과 한글 글리프의 대응 관계**를 복원합니다.
2. Switch 원본 OTF/TTF를 기반으로 유지하면서 한글 윤곽선과 메트릭을 추가합니다.
3. PC 패치 문자열이 실제 한글 Unicode 대신 CJK 코드 슬롯을 사용한다면, 그 CJK 슬롯을 대응 한글 글리프에 다시 연결합니다.

즉, G1N은 매핑과 모양을 읽는 근거이고 Switch 원본 OTF/TTF는 최종 파일의 뼈대입니다.

## Arland DX PC 패치에서 재검증한 값

이번 저장소를 만들면서 실제 작업 파일로 다시 검사한 결과입니다.

- G1N 크기: 22,778,776바이트
- 헤더 크기: `0x2624`
- 비트맵 풀 시작: `0x77698`
- 팔레트 수: 152
- 서브폰트 테이블 수: 1
- 글리프 레코드 수: 29,023
- non-zero charmap 엔트리: 29,022
- 패치 전후 윤곽선이 달라진 슬롯: 2,360
- 한글 donor 윤곽선과 정확히 대응된 슬롯: 2,360
- 미일치/모호한 대응: 0/0

Switch 원본 4종 중 `FOT-ChiaroStd-B_0.otf`는 CFF, `Tuffy.ttf`, `Uhei00m.ttf`, `UMIN00L.ttf`는 TrueType `glyf` 계열이므로 같은 삽입 방식을 네 파일에 무조건 적용하면 안 됩니다.

## G1N에서 확인할 값

일반적으로 확인된 `_N1G0000` 변형의 주요 필드는 다음과 같습니다.

```text
0x00  8 bytes  magic/version: _N1G0000
0x08  u32       declared file size
0x0C  u32       header size / first table offset
0x10  u32       palette-related entry value (게임별 차이 가능)
0x14  u32       bitmap atlas pool offset
0x18  u32       palette count
0x1C  u32       subfont/table count
0x20  u32[]     table offsets
```

각 테이블은 BMP 문자 영역을 다루는 `u16[0x10000]` charmap 뒤에 고정 길이 글리프 레코드가 오는 형태가 확인됐습니다. 게임과 G1N 버전에 따라 메트릭·비트맵 형식이 달라질 수 있으므로 필드값을 수정하기 전에 해당 파일의 구조를 검증해야 합니다.

```powershell
python tools/g1n_inspect.py ArlandDX_font_jp.g1n
```

## 1. 글꼴 네 개를 먼저 조사

메뉴·대사·도감 등 화면마다 다른 폰트를 사용할 수 있으므로 한 파일만 고치면 일부 화면에 깨진 글자가 남습니다.

```powershell
python tools/font_inventory.py `
  FOT-ChiaroStd-B_0.otf Tuffy.ttf Uhei00m.ttf UMIN00L.ttf
```

확인할 항목:

- TrueType `glyf`인지 CFF `CFF `인지
- unitsPerEm
- Unicode cmap 형식(4/12/13)
- 한글 음절·호환 자모·CJK 슬롯 범위
- 세로 메트릭 `vhea`/`vmtx` 존재 여부

## 2. CJK 슬롯 → 한글 매핑 복원

패치 전 글꼴과 PC 패치 글꼴에서 같은 코드포인트의 윤곽선이 달라진 슬롯을 찾고, 그 윤곽선을 한글 donor 글꼴과 비교합니다.

```powershell
python tools/recover_outline_mapping.py `
  original_converted.ttf pc_patch_converted.ttf KoreanDonor.ttf mapping.json
```

자동 결과 중 `unmatched`와 `ambiguous`가 0인지 확인해야 합니다. 윤곽선 변환 과정에서 좌표나 곡선 형식이 바뀌었다면 정확 일치 방식은 실패할 수 있으므로 이미지 렌더 비교나 별도 정규화가 필요합니다.

매핑 파일 형식:

```json
{
  "mapping": {
    "U+4E00": "U+AC00"
  }
}
```

## 3. Switch TrueType 기반 폰트 생성

`glyf` 테이블을 가진 Switch TTF 또는 TrueType-flavored OTF는 donor 윤곽선을 추가할 수 있습니다.

```powershell
python tools/build_truetype_slot_font.py `
  SwitchOriginal.ttf KoreanDonor.ttf mapping.json SwitchKorean.ttf `
  --also-unicode
```

도구는 다음을 수행합니다.

- donor와 target의 unitsPerEm 차이만큼 윤곽선과 수평 메트릭 배율 조정
- 복합 글리프 분해
- cubic 윤곽선을 quadratic으로 변환
- 기존 CJK 슬롯을 새 한글 글리프로 연결
- 선택적으로 실제 한글 Unicode 코드도 같은 글리프에 연결
- 세로 메트릭이 있으면 새 글리프용 값을 생성

## 4. CFF OTF 처리

`OTTO`/`CFF ` 기반 OTF에는 TrueType `glyf` 객체를 그대로 넣으면 안 됩니다. 이번 작업에서는 정상 변환된 한글 CFF OTF를 기준으로 사용하고, 필요한 슬롯 별칭만 cmap에 추가했습니다.

```powershell
python tools/alias_font_slots.py FullHangulCFF.otf mapping.json SwitchAliased.otf
```

CFF 윤곽선 자체를 새로 생성해야 한다면 CFF-aware 빌드 과정이 별도로 필요합니다. 이 저장소의 TrueType 삽입 도구를 CFF에 강제로 사용하지 마세요.

## 5. 검증

- 결과 글꼴을 fontTools로 다시 열 수 있어야 합니다.
- 목표 슬롯 수와 실제 별칭 수가 같아야 합니다.
- 원본 비대상 cmap 항목과 UI용 라틴 글리프가 유지되어야 합니다.
- 네 글꼴 모두 한글 문장과 실제 glyph-slot 문자열로 렌더 미리보기를 확인합니다.
- 게임에서는 대사, 메뉴, 도감, 도움말 등 서로 다른 화면을 확인합니다.
- 항상 부팅되는 이전 글꼴 묶음을 보존합니다.

## 외부 참고 구현

- [G1N Font Editor](https://github.com/lehieugch68/G1N-Font-Editor): G1N 편집 및 TrueType 글리프 비트맵 생성 도구
- [nobunaga-shinsei-korean-patch 형식 기록](https://github.com/snake7594/nobunaga-shinsei-korean-patch/blob/main/docs/FORMATS.md): `_N1G0000` 계열 G1N 구조 연구 사례

두 자료는 구조 확인을 위한 참고 링크이며, 이 저장소 도구는 해당 프로젝트 코드를 복사하지 않고 별도로 작성했습니다.

