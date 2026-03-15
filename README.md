# DumpCache

쓸모없는 커뮤니티의 잉여 데이터를 수집하는 도구입니다.

## 🚀 빠른 시작

### 1. 환경 설정

`.env.example` 파일을 `.env`로 복사하고 설정을 입력합니다.

```bash
cp .env.example .env
```

`.env` 파일을 편집기로 열어서 설정을 수정합니다:

```bash
nano .env
# 또는
vim .env
# 또는 VSCode 등 원하는 에디터 사용
```

**필수 설정:**
- `GALLERY_URL`: 수집할 갤러리 주소 (전체 URL 복사-붙여넣기)
- `CRAWL_INTERVAL`: 수집 간격 (초 단위, 기본값: 60)

### 2. Docker 컨테이너 실행

```bash
# 백그라운드로 실행
docker compose up -d

# 로그 확인
docker compose logs -f

# 중지
docker compose down
```

## 📁 디렉토리 구조

```
DumpCache/
├── data/
│   ├── images/          # 다운로드된 이미지 저장 (볼륨 마운트)
│   └── metadata.db      # 수집 이력 데이터베이스
├── .env                 # 환경 설정 파일 (직접 작성)
├── .env.example         # 환경 설정 템플릿
├── docker-compose.yml   # Docker Compose 설정
└── crawler.py           # 크롤러 메인 코드
```

## ⚙️ 환경 변수

| 변수 | 설명 | 예시 |
|------|------|------|
| `GALLERY_URL` | 갤러리 주소 (전체 URL) | `https://gall.dcinside.com/board/lists/?id=dcbest` |
| `CRAWL_INTERVAL` | 수집 간격 (초) | `60` (1분) |
| `IMAGE_SAVE_PATH` | 이미지 저장 경로 | `/app/data/images` (기본값) |
| `METADATA_DB_PATH` | 메타데이터 DB 경로 | `/app/data/metadata.db` (기본값) |

## 🔄 재시작 및 업데이트

```bash
# 코드 수정 후 재빌드
docker compose up -d --build

# 컨테이너 재시작
docker compose restart

# 설정(.env) 변경 시
docker compose down
docker compose up -d
```

## 📊 로그 확인

```bash
# 실시간 로그 확인
docker compose logs -f

# 최근 100줄 로그
docker compose logs --tail=100

# 크롤러 컨테이너만 확인
docker compose logs -f dumpcache-crawler
```

## 🛑 중지 및 삭제

```bash
# 중지 (컨테이너 삭제, 데이터는 유지)
docker compose down

# 완전 삭제 (이미지 포함)
docker compose down --rmi all

# 데이터까지 삭제 (주의!)
docker compose down -v
```

## 🧪 테스트

크롤러를 실행하기 전에 설정이 올바른지 검증할 수 있습니다.

```bash
# 통합 검증 테스트 실행
docker compose run --rm dumpcache-crawler python test_crawler.py
```

**검증 항목:**
- ✅ 공지사항/광고/설문 필터링
- ✅ 이미지/영상 포함 여부 검출
- ✅ 게시글 파싱 정상 작동

테스트는 `.env` 파일의 `GALLERY_URL` 설정을 사용합니다.

## 🐛 문제 해결

### 이미지가 다운로드되지 않아요
- `.env` 파일에서 `GALLERY_URL`이 올바른지 확인하세요
- 로그를 확인하여 에러 메시지를 확인하세요: `docker compose logs -f`
- 테스트 스크립트로 검증하세요: `docker compose run --rm dumpcache-crawler python test_crawler.py`

### 컨테이너가 계속 재시작돼요
- 갤러리 URL이 잘못되었거나 접근할 수 없는 경우일 수 있습니다
- 로그에서 에러 원인을 확인하세요

### 다운로드한 이미지가 보이지 않아요
- `./data/images/` 폴더를 확인하세요
- 볼륨 마운트가 제대로 되었는지 확인하세요

## 📄 라이선스

MIT License
