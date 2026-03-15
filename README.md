# DumpCache

쓸모없는 커뮤니티의 잉여 데이터를 수집하는 도구입니다.

## 🚀 빠른 시작

### 방법 1: GitHub Release 사용 (권장)

최신 릴리즈에서 필요한 파일을 다운로드하여 바로 실행할 수 있습니다.

```bash
# 최신 버전 자동 다운로드
curl -L -O https://github.com/HelloJamong/DumpCache/releases/latest/download/docker-compose.yml
curl -L -O https://github.com/HelloJamong/DumpCache/releases/latest/download/default.env.example

# 또는 특정 버전 다운로드 (버전 확인: https://github.com/HelloJamong/DumpCache/releases)
# VERSION=v1.0.1
# curl -L -O https://github.com/HelloJamong/DumpCache/releases/download/${VERSION}/docker-compose.yml
# curl -L -O https://github.com/HelloJamong/DumpCache/releases/download/${VERSION}/default.env.example

# 데이터 디렉토리 생성
mkdir -p data/images

# .env 파일 생성 및 설정
cp default.env.example .env
nano .env  # 갤러리 URL 등 필수 설정 입력

# 실행 (Docker Compose v2)
docker compose up -d

# 또는 Docker Compose v1 (Synology NAS 등)
# docker-compose up -d

# 로그 확인
docker compose logs -f  # v2
# docker-compose logs -f  # v1
```

**필수 설정 (`.env` 파일):**
- `GALLERY_URL`: 수집할 갤러리 주소 (전체 URL 복사-붙여넣기)
- `CRAWL_INTERVAL`: 수집 간격 (초 단위, 기본값: 60)

### 방법 2: 저장소 클론 (개발용)

```bash
# 저장소 클론
git clone https://github.com/HelloJamong/DumpCache.git
cd DumpCache

# .env 파일 생성 및 설정
cp default.env.example .env
nano .env  # 갤러리 URL 등 필수 설정 입력

# Docker 이미지 빌드
docker build -t dumpcache-local .

# 실행 (로컬 빌드 이미지 사용)
docker run -d \
  --name dumpcache-crawler \
  --restart unless-stopped \
  --env-file .env \
  -v ./data:/app/data \
  dumpcache-local

# 로그 확인
docker logs -f dumpcache-crawler
```

### Docker Hub에서 이미지 직접 사용

```bash
# 최신 버전
docker pull igor0670/dumpcache:latest

# 특정 버전
docker pull igor0670/dumpcache:v1.0.0
```

### 중지

```bash
docker compose down     # v2
# docker-compose down   # v1
```

## 📁 디렉토리 구조

```
DumpCache/
├── data/
│   ├── images/          # 다운로드된 이미지 저장 (볼륨 마운트)
│   └── metadata.db      # 수집 이력 데이터베이스
├── .env                 # 환경 설정 파일 (직접 작성)
├── default.env.example  # 환경 설정 템플릿
├── docker-compose.yml   # Docker Compose 설정 (Docker Hub 이미지 사용)
├── Dockerfile           # Docker 이미지 빌드 파일 (개발용)
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
# 최신 이미지로 업데이트 (릴리즈 버전 사용 시)
docker compose pull        # v2
docker compose up -d

# 또는
# docker-compose pull      # v1
# docker-compose up -d

# 컨테이너 재시작
docker compose restart     # v2
# docker-compose restart   # v1

# 설정(.env) 변경 시
docker compose down
docker compose up -d
```

### 개발 모드 (로컬 빌드)

```bash
# 코드 수정 후 재빌드
docker build -t dumpcache-local .
docker stop dumpcache-crawler
docker rm dumpcache-crawler
docker run -d \
  --name dumpcache-crawler \
  --restart unless-stopped \
  --env-file .env \
  -v ./data:/app/data \
  dumpcache-local
```

## 📊 로그 확인

```bash
# 실시간 로그 확인
docker compose logs -f              # v2
# docker-compose logs -f            # v1

# 최근 100줄 로그
docker compose logs --tail=100      # v2
# docker-compose logs --tail=100    # v1

# 크롤러 컨테이너만 확인
docker compose logs -f dumpcache-crawler     # v2
# docker-compose logs -f dumpcache-crawler   # v1
```

## 🛑 중지 및 삭제

```bash
# 중지 (컨테이너 삭제, 데이터는 유지)
docker compose down              # v2
# docker-compose down            # v1

# 완전 삭제 (이미지 포함)
docker compose down --rmi all    # v2
# docker-compose down --rmi all  # v1

# 데이터까지 삭제 (주의!)
docker compose down -v           # v2
# docker-compose down -v         # v1
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
