# 소닉 애니메이션 뷰어

[PRD.md](PRD.md)에 따라 Python과 pico2d로 구현한 단일 파일 애니메이션 뷰어입니다. 원본 시트의 소닉 포즈 76개를 14개 동작으로 등록했습니다.

## 실행

Python과 pico2d가 필요합니다. 검증 환경은 Windows, Python 3.14.7, pico2d 1.5.1입니다.

저장소 루트에서 실행합니다.

```powershell
python -m pip install pico2d
python Labs/LEC09/sonic_animation_viewer.py
```

실습 폴더에서는 `python sonic_animation_viewer.py`로 실행합니다. 이미지 경로는 실행 파일 위치를 기준으로 합니다.

각 동작을 **5회 재생 → 마지막 프레임에서 1초 정지 → 다음 동작 전환** 순서로 무한 반복합니다. 기본 속도는 12 FPS이며, 800×600 창에 6배 확대하여 표시합니다. ESC 키 또는 창 닫기로 종료합니다.

## 검수 옵션

```powershell
python Labs/LEC09/sonic_animation_viewer.py --trace --cycles 2
python Labs/LEC09/sonic_animation_viewer.py --seconds 3
```

- `--trace`: 동작 시작, 반복 완료, 정지 시작의 누적 재생 시간을 콘솔에 기록합니다.
- `--cycles N`: 전체 동작을 N회 순환한 뒤 종료합니다. 생략하면 무한 반복합니다.
- `--seconds N`: N초 후 종료하는 실행 확인용 옵션입니다.

동작 이름은 원본에 이름 표기가 없어 화면의 자세를 설명하도록 붙였습니다. 제목·제작자 문구와 하단의 정적 캐릭터는 재생 대상에서 제외했습니다.

[검수 결과](evidence/acceptance.md), [전체 프레임 검수 이미지](evidence/frames.png), [실제 렌더링 이미지](evidence/viewer.png)를 확인할 수 있습니다.
