# DumpCache - Project Guidelines

## 프로젝트 개요

커뮤니티 웹사이트에서 이미지를 자동으로 수집하는 Docker 기반 크롤러입니다.

## 핵심 원칙

### 1. 실행 환경
- **Docker 컨테이너 기반**: 모든 서비스는 Docker를 통해 작동
- **백그라운드 실행**: 서버에서 데몬 형태로 지속 실행
- **Docker Compose V2**: 모든 명령어는 `docker compose` (v2) 양식 사용
  - ❌ `docker-compose` (v1)
  - ✅ `docker compose` (v2)

### 2. 보안 및 개인정보
- **익명성 유지**: 코드 및 문서에서 특정 커뮤니티 이름을 직접 노출하지 않음
- **예시 데이터**: 모든 예시 URL, 갤러리 ID는 공란 또는 일반적인 placeholder 사용
  - ❌ `https://gall.dcinside.com/board/lists/?id=dcbest`
  - ✅ `갤러리 주소 입력` 또는 공란

### 3. 봇 차단 회피 (CRITICAL)

**필수 구현 사항:**

#### A. Rate Limiting (속도 제한)
- 요청 간 최소 간격 보장 (기본: 1분)
- 랜덤 지연 추가로 패턴 탐지 회피
- 설정 가능한 `CRAWL_INTERVAL` 환경 변수

#### B. User-Agent 및 헤더 설정
- 실제 브라우저처럼 보이는 User-Agent 사용
- 필수 헤더 포함:
  - `User-Agent`: 최신 브라우저 정보
  - `Accept`: 다양한 MIME 타입
  - `Accept-Language`: 한국어 우선
  - `Referer`: 적절한 참조 페이지
  - `Connection`: keep-alive
  - `DNT`: 1

#### C. 요청 패턴 다양화
- 고정된 시간 간격 대신 랜덤 간격 사용
- 예: 60초 ± 10초 범위 내 랜덤

#### D. 에러 처리 및 백오프
- HTTP 429 (Too Many Requests) 감지 시 자동 대기
- 연속 실패 시 지수 백오프 (exponential backoff) 적용
- 최대 재시도 횟수 제한

#### E. IP 차단 대응
- 차단 감지 시 로그 기록 및 대기
- 재시도 전 충분한 대기 시간 확보

### 4. 파일 구조

```
DumpCache/
├── .claude/
│   └── CLAUDE.md              # 프로젝트 가이드라인 (이 파일)
├── .git/                      # Git 저장소
├── data/                      # 데이터 디렉토리 (볼륨 마운트)
│   ├── images/               # 다운로드된 이미지 저장
│   └── metadata.db           # SQLite 데이터베이스 (수집 이력)
├── .env                       # 환경 변수 (git 제외)
├── .env.example               # 환경 변수 템플릿
├── .gitignore                 # Git 제외 파일 목록
├── crawler.py                 # 메인 크롤러 로직
├── docker-compose.yml         # Docker Compose 설정 (v2)
├── Dockerfile                 # Docker 이미지 빌드 파일
├── LICENSE                    # 라이선스
├── README.md                  # 사용자 가이드
├── requirements.txt           # Python 의존성
└── origin_src.py              # 기존 소스 (git 제외, 참고용)
```

### 5. 코드 작성 규칙

#### Python 코드
- **타입 힌팅**: 가능한 경우 타입 힌트 사용
- **에러 처리**: 모든 네트워크 요청에 try-except 적용
- **로깅**: `logging` 모듈 사용 (print 사용 금지)
  - INFO: 정상 동작 정보
  - WARNING: 재시도 가능한 에러
  - ERROR: 치명적 에러
- **환경 변수**: `python-dotenv`로 `.env` 로딩

#### Docker
- **멀티 스테이지 빌드**: 필요 시 사용하여 이미지 크기 최소화
- **보안**: 루트 권한 최소화
- **로그 로테이션**: 로그 파일 크기 제한 설정

### 6. 데이터 관리

#### 이미지 저장
- 파일명: 고유 식별자 기반
- 중복 체크: 파일 해시(MD5 또는 SHA256) 사용
- 충돌 처리: 파일명 중복 시 `-1`, `-2` 등 접미사 추가

#### 메타데이터 DB (SQLite)
- **테이블 구조**:
  - `images`: 수집된 이미지 정보
    - `id`: Primary Key
    - `file_hash`: 파일 해시 (중복 체크용)
    - `file_name`: 저장된 파일명
    - `file_path`: 전체 경로
    - `original_url`: 원본 이미지 URL
    - `post_url`: 게시글 URL
    - `post_id`: 게시글 ID
    - `downloaded_at`: 다운로드 시각 (ISO 8601)
  - `crawl_history`: 크롤링 이력
    - `id`: Primary Key
    - `crawled_at`: 크롤링 시각
    - `posts_found`: 발견한 게시글 수
    - `images_downloaded`: 다운로드한 이미지 수
    - `errors`: 에러 발생 횟수

### 7. 환경 변수

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `GALLERY_URL` | ✅ | - | 갤러리 전체 URL |
| `CRAWL_INTERVAL` | ❌ | 60 | 수집 간격 (초) |
| `IMAGE_SAVE_PATH` | ❌ | /app/data/images | 이미지 저장 경로 |
| `METADATA_DB_PATH` | ❌ | /app/data/metadata.db | DB 파일 경로 |
| `MAX_POSTS_PER_CYCLE` | ❌ | 10 | 한 번에 처리할 최대 게시글 수 |
| `DEBUG` | ❌ | False | 디버그 모드 |

### 8. 개발 워크플로우

#### 초기 설정
```bash
# 1. .env 파일 생성
cp .env.example .env
nano .env  # 설정 입력

# 2. Docker 빌드 및 실행
docker compose up -d --build

# 3. 로그 확인
docker compose logs -f
```

#### 코드 수정 시
```bash
# 1. 컨테이너 중지
docker compose down

# 2. 코드 수정

# 3. 재빌드 및 실행
docker compose up -d --build
```

#### 디버깅
```bash
# 로그 확인
docker compose logs -f dumpcache-crawler

# 컨테이너 내부 접근
docker compose exec dumpcache-crawler /bin/bash

# 데이터베이스 확인
docker compose exec dumpcache-crawler sqlite3 /app/data/metadata.db "SELECT * FROM images LIMIT 10;"
```

### 9. 금지 사항

❌ **절대 하지 말 것**:
- DDoS 공격으로 간주될 수 있는 과도한 요청
- 봇 차단 우회 로직 없이 크롤링 실행
- 개인정보 또는 민감한 데이터 수집
- 저작권 침해 가능성 있는 데이터 재배포
- 특정 커뮤니티 이름을 코드/문서에 하드코딩

### 10. Git 관리

#### .gitignore 필수 항목
- `.env` (환경 변수)
- `origin_src.py` (기존 소스)
- `data/` (수집된 데이터)
- `*.db`, `*.sqlite` (데이터베이스)
- `__pycache__/`, `*.pyc` (Python 캐시)
- `.vscode/`, `.idea/` (IDE 설정)

#### 커밋 메시지 규칙
- `feat:` 새로운 기능
- `fix:` 버그 수정
- `docs:` 문서 변경
- `refactor:` 코드 리팩토링
- `chore:` 기타 작업

## 참고 사항

- 이 프로젝트는 **교육 목적**으로만 사용되어야 합니다
- 크롤링 대상 웹사이트의 `robots.txt` 및 이용약관을 준수하세요
- 과도한 요청으로 인한 서비스 장애를 유발하지 마세요
- 수집한 데이터의 사용 및 배포는 사용자 책임입니다
