# Directory Tree Viewer - 프로젝트 기획안

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | Directory Tree Viewer |
| **목적** | 실행 위치 기준 디렉토리 구조를 GUI 트리로 시각화하고, 검색 및 탐색기 연동 기능 제공 |
| **플랫폼** | Windows 11 (단일 실행파일 배포) |
| **Python 버전** | 3.12 |
| **빌드 도구** | PyInstaller 6.x |

---

## 2. 기술 스택 선정

### 2.1 GUI 프레임워크: **tkinter (ttk)**

| 비교 항목 | tkinter | PySide6/PyQt6 | customtkinter | Dear PyGui |
|-----------|---------|---------------|---------------|------------|
| 트리 위젯 품질 | **Good** (ttk.Treeview) | Excellent | Poor (ttk 폴백) | Poor |
| Windows 11 네이티브 룩 | 양호 (vista 테마) | 매우 좋음 | 좋음 (트리 제외) | 비네이티브 |
| 지연 로딩 | 수동 (간단) | 내장 (QFileSystemModel) | tkinter 동일 | 수동 (어려움) |
| 검색/필터 | 단순 순회 | QSortFilterProxyModel | tkinter 동일 | 수동 |
| PyInstaller EXE 크기 | **8~15 MB** | 40~80 MB | 15~25 MB | 20~35 MB |
| 시작 속도 | **빠름** | 느림 (--onefile 시 2~5초) | 빠름 | 보통 |
| 패키징 안정성 | **최고** | 문제 빈발 | 좋음 | 보통 |

**선정 이유:**
- `ttk.Treeview`가 이 프로젝트의 핵심 기능(계층 표시, 컬럼, 펼치기/접기, 아이콘)을 모두 내장 지원
- Python 내장 모듈이므로 외부 의존성 없음 (pip install 불필요)
- PyInstaller 빌드 시 가장 작은 EXE, 가장 빠른 시작, 가장 적은 패키징 문제
- 유틸리티 도구 특성상 Qt의 UI 폴리시보다 실용성이 우선

### 2.2 빌드 도구: **PyInstaller >= 6.0**

- Python 3.12 완전 지원 (6.x 시리즈)
- 최신 안정 버전: **6.19.0**
- `--onefile --windowed` 모드로 단일 EXE 생성

### 2.3 탐색기 연동: **subprocess.Popen**

```python
subprocess.Popen(['explorer', '/select,', path])
```

- `/select,` 플래그로 파일/폴더를 **선택된 상태**로 탐색기 열기
- `os.startfile()`보다 우수 (특정 항목 하이라이트 가능)
- `Popen` 사용으로 GUI 블로킹 방지

---

## 3. 핵심 기능 명세

### 3.1 MVP (필수 기능)

| # | 기능 | 설명 |
|---|------|------|
| 1 | **트리 표시** | 실행 위치 기준 폴더/파일 계층 구조 표시 (펼치기/접기) |
| 2 | **지연 로딩** | 폴더 펼칠 때만 하위 항목 스캔 (성능 최적화) |
| 3 | **파일 정보 컬럼** | 이름, 크기(읽기 좋은 형식), 수정일 |
| 4 | **검색 바** | 실시간 필터링 (150~300ms 디바운스), 매치 결과 하이라이트 |
| 5 | **검색 결과 카운트** | "N matches" 표시 |
| 6 | **탐색기 열기 버튼** | "Open in Explorer" 버튼 (`/select,` 모드) |
| 7 | **경로 복사** | "Copy Path" 버튼 - 절대 경로를 클립보드에 복사 |
| 8 | **상태 바** | "Files: 1,247 | Folders: 89 | Root: ..." 형식 |
| 9 | **새로고침** | "Refresh" 버튼 - 현재 루트 디렉토리 재스캔 |
| 10 | **기본 제외 패턴** | `node_modules`, `.git`, `__pycache__` 등 자동 제외 |
| 11 | **키보드 내비게이션** | 화살표 키 탐색, Enter 펼치기/접기, Ctrl+F 검색 포커스 |

### 3.2 Nice-to-Have (후순위)

| # | 기능 |
|---|------|
| 1 | 다크/라이트 테마 토글 |
| 2 | 정렬 옵션 (이름, 크기, 수정일) |
| 3 | 우클릭 컨텍스트 메뉴 |
| 4 | .gitignore 패턴 자동 적용 |
| 5 | 제외 패턴 커스터마이징 UI |
| 6 | 트리 구조 텍스트 내보내기 |

---

## 4. UI/UX 설계

> **UI 언어: 영어 (English)**
> 모든 버튼 라벨, 상태 메시지, 검색 플레이스홀더 등 사용자에게 보이는 텍스트는 영어로 표시합니다.

### 4.1 레이아웃

```
┌─────────────────────────────────────────────────────────┐
│  Directory Tree Viewer                       [─][□][✕]  │
├─────────────────────────────────────────────────────────┤
│  Root: C:\Users\...\project                             │
│  [Search ______________________________] [X]  N matches │
├─────────────────────────────────────────────────────────┤
│  📁 src                                                 │
│   ├── 📁 components                                     │
│   │    ├── 📄 Header.tsx          2.1 KB   2024-03-01   │
│   │    └── 📄 Footer.tsx          1.5 KB   2024-03-01   │
│   └── 📄 main.py                  3.2 KB   2024-03-02   │
│  📁 tests                                               │
│  📄 README.md                     0.8 KB   2024-02-28   │
│  📄 requirements.txt              0.1 KB   2024-02-28   │
├─────────────────────────────────────────────────────────┤
│  [Open in Explorer]  [Copy Path]  [Refresh]             │
├─────────────────────────────────────────────────────────┤
│  Files: 1,247 | Folders: 89 | Root: C:\...\project      │
└─────────────────────────────────────────────────────────┘
```

### 4.2 디자인 원칙

- **Windows 11 네이티브 룩**: `ttk` vista/winnative 테마 사용
- **가독성 우선**: 적절한 들여쓰기 (20px/레벨), 폴더/파일 구분 아이콘
- **반응성**: 부분 결과 즉시 표시, 풀 스캔 완료 대기 없음
- **미니멀 크롬**: 트리 콘텐츠가 윈도우의 대부분 차지, 도구바/상태바는 컴팩트 (28px)

### 4.3 검색 UX

- **실시간 필터링**: 타이핑하면 매치 항목과 그 상위 폴더만 표시
- **하이라이트**: 매칭 문자열 부분에 선택 표시
- **디바운스**: 200ms 지연 후 필터 적용 (타이핑 중 UI 멈춤 방지)
- **결과 카운트**: 검색바 옆에 "N matches" 실시간 표시
- **자동 펼치기**: 검색 결과가 포함된 모든 브랜치 자동 확장

---

## 5. 성능 전략

### 5.1 스캔 전략: 하이브리드

| 전략 | 적용 |
|------|------|
| 초기 로딩 | 루트부터 3~4레벨까지 즉시 스캔 |
| 깊은 디렉토리 | 펼칠 때 온디맨드 로딩 |
| 검색 시 | 백그라운드 스레드에서 전체 스캔 |

### 5.2 기본 제외 디렉토리

```
node_modules, .git, __pycache__, .pytest_cache,
.next, .nuxt, dist, build, out, .venv, venv,
.DS_Store, Thumbs.db, *.pyc, *.o, *.obj
```

### 5.3 성능 목표

| 디렉토리 규모 | 목표 스캔 시간 |
|--------------|--------------|
| ~1,000 파일 | < 100ms |
| ~10,000 파일 | < 500ms |
| ~50,000 파일 | < 2초 |
| 100,000+ 파일 | < 5초 (프로그레스 표시) |

### 5.4 스레딩

- 디렉토리 스캔은 **별도 스레드**에서 실행 (UI 블로킹 방지)
- `threading.Thread` + `queue.Queue`로 UI 스레드에 결과 전달
- 검색 중 재검색 시 이전 작업 취소

---

## 6. 환경 구축 가이드

### 6.1 사전 요구사항

- Python 3.12 설치 (python.org 공식 설치 프로그램)
- Git (선택사항, 버전 관리용)

### 6.2 원커맨드 세팅 (make.bat)

```bat
:: CMD 또는 PowerShell에서:
make.bat setup
```

이 한 줄로 아래가 모두 자동 실행됩니다:
1. Python 3.12 가상환경 생성 (`.venv/`)
2. pip 최신 버전 업그레이드
3. requirements-dev.txt 의존성 전체 설치

### 6.3 수동 활성화 (직접 개발 시)

```bash
# Git Bash
source .venv/Scripts/activate

# CMD
.venv\Scripts\activate.bat

# PowerShell
.venv\Scripts\Activate.ps1
```

> **참고:** `make.bat run`, `make.bat build`는 venv 활성화 없이도 내부적으로 `.venv\Scripts\python.exe`를 직접 호출하므로, 수동 활성화는 직접 pip 설치 등을 할 때만 필요합니다.

### 6.4 requirements.txt

```
# requirements.txt (런타임)
Pillow>=10.0

# requirements-dev.txt (개발/빌드)
-r requirements.txt
pyinstaller>=6.0
```

---

## 7. 프로젝트 구조

```
directory_tree/
├── .venv/                    # Python 3.12 가상환경
├── src/
│   └── directory_tree/
│       ├── __init__.py
│       ├── main.py           # 엔트리포인트
│       ├── app.py            # 메인 Application 클래스
│       ├── tree_scanner.py   # 디렉토리 스캔 로직
│       ├── search.py         # 검색/필터 로직
│       └── utils.py          # 유틸리티 (경로 처리, 포맷팅 등)
├── assets/
│   └── app.ico               # 앱 아이콘
├── docs/
│   └── plan/
│       └── project-plan.md   # 이 기획안
├── make.bat                  # 빌드 시스템 (setup/run/build/clean)
├── DirectoryTree.spec        # PyInstaller spec 파일 (빌드 시 자동 생성)
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
└── README.md
```

---

## 8. 빌드 및 배포

### 8.1 make.bat - 원커맨드 빌드 시스템

우분투의 Makefile처럼, `make.bat` 하나로 모든 작업을 처리합니다.

```
make.bat [command]

Commands:
  setup     가상환경 생성 (Python 3.12) + 의존성 설치
  run       앱 실행
  build     PyInstaller로 단일 EXE 빌드
  rebuild   clean + build
  clean     빌드 산출물 삭제 (build/, dist/)
  freeze    pip 패키지 목록을 requirements.txt로 내보내기
  help      도움말 표시
```

**사용 흐름 (처음부터 끝까지 3줄):**

```bat
make.bat setup     :: 1회만 - 가상환경 + 의존성
make.bat run       :: 개발 중 실행
make.bat build     :: dist\DirectoryTree.exe 생성
```

### 8.2 make.bat 내부 동작

| 커맨드 | 실행 내용 |
|--------|----------|
| `setup` | `py -3.12 -m venv .venv` → pip 업그레이드 → requirements 설치 |
| `run` | `.venv\Scripts\python.exe src\directory_tree\main.py` |
| `build` | `.spec` 파일 있으면 사용, 없으면 `--onefile --windowed` 로 새로 빌드 |
| `clean` | `build/`, `dist/`, 모든 `__pycache__/` 삭제 |
| `rebuild` | clean → build 순차 실행 |
| `freeze` | `pip freeze > requirements.txt` |

### 8.3 주요 빌드 옵션

| 옵션 | 설명 |
|------|------|
| `--onefile` | 단일 EXE 파일 생성 (배포 간편) |
| `--windowed` | 콘솔 창 숨김 (GUI 앱) |
| `--icon=app.ico` | EXE에 아이콘 임베드 (assets/app.ico 존재 시 자동 적용) |
| `--name DirectoryTree` | 출력 파일명 |

### 8.4 예상 EXE 크기

| 모드 | 예상 크기 |
|------|----------|
| `--onefile` (tkinter only) | **10~15 MB** |
| `--onefile` (tkinter + Pillow) | **15~20 MB** |
| `--onedir` 전체 | 8~15 MB |

### 8.5 배포 시 주의사항

| 이슈 | 설명 | 대응 |
|------|------|------|
| **Windows Defender/SmartScreen** | PyInstaller EXE는 서명 없으면 경고 발생 | EV 코드서명($400~700/년) 또는 사용자에게 안내 |
| **AV 오탐** | PyInstaller의 자가 추출 패턴이 악성코드로 오인 | UPX 미사용 권장, `--onedir`가 `--onefile`보다 오탐 적음 |
| **콜드 스타트** | `--onefile`은 매 실행 시 temp에 추출 (2~5초) | 개인 사용은 `--onedir` 권장 |
| **배포 형태 대안** | Inno Setup 등으로 설치 프로그램 제작 가능 | `--onedir` + 설치 프로그램이 가장 안정적 |

---

## 9. 구현 로드맵

### Phase 1: 기반 구축
1. 가상환경 생성 및 의존성 설치
2. 프로젝트 구조 생성
3. tkinter 기본 윈도우 + ttk.Treeview 셋업

### Phase 2: 핵심 기능
4. 디렉토리 스캔 및 트리 표시 (지연 로딩)
5. 파일 정보 컬럼 (크기, 수정일)
6. 탐색기 열기 기능
7. 경로 복사 기능

### Phase 3: 검색
8. 검색 바 UI
9. 실시간 필터링 + 디바운스
10. 검색 결과 하이라이트 및 카운트

### Phase 4: 마감
11. 상태 바, 새로고침, 키보드 단축키
12. 기본 제외 패턴 적용
13. 아이콘 및 UI 폴리싱

### Phase 5: 빌드 및 배포
14. PyInstaller spec 파일 작성
15. 단일 EXE 빌드 및 테스트
16. 다른 Windows 11 PC에서 동작 확인

---

## 10. 기술적 핵심 구현 포인트

### 10.1 지연 로딩 패턴 (ttk.Treeview)

```python
# 폴더 삽입 시 더미 자식 추가
tree.insert(parent, 'end', text='folder_name', open=False)
tree.insert(folder_id, 'end', text='__dummy__')  # 펼침 화살표 표시용

# 펼칠 때 실제 스캔
def on_open(event):
    item = tree.focus()
    children = tree.get_children(item)
    if len(children) == 1 and tree.item(children[0], 'text') == '__dummy__':
        tree.delete(children[0])
        scan_and_populate(item)

tree.bind('<<TreeviewOpen>>', on_open)
```

### 10.2 검색 필터링

```python
# 전체 스캔 후 필터 결과만 트리에 표시
# 매치 항목 + 상위 폴더 경로를 보존
def filter_tree(query):
    matches = [f for f in all_files if query.lower() in f.name.lower()]
    # 매치된 파일의 모든 조상 폴더도 포함
    visible = set()
    for match in matches:
        path = match
        while path != root:
            visible.add(path)
            path = path.parent
    rebuild_tree(visible)
```

### 10.3 탐색기 열기

```python
import subprocess

def open_in_explorer(path):
    subprocess.Popen(['explorer', '/select,', str(path)])
```

---

## 11. 요약

- **GUI**: tkinter (ttk.Treeview) - 내장 모듈, 최소 의존성, 최소 EXE 크기
- **검색**: 실시간 필터링 + 디바운스 + 결과 카운트
- **탐색기 연동**: `subprocess.Popen(['explorer', '/select,', path])`
- **빌드**: PyInstaller 6.x `--onefile --windowed` → 단일 EXE (~10~15MB)
- **성능**: 하이브리드 스캔 (초기 3~4레벨 + 온디맨드) + 백그라운드 스레딩
- **배포**: 어떤 Windows 11 PC에서든 실행 가능한 단일 EXE 파일
