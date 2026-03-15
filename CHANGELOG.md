# Changelog

## [1.0.1] - 2026-03-15

### Changed
- 환경 변수 예시 파일명 변경: `.env.example` → `default.env.example`
  - 더 명확한 파일명으로 사용자 혼동 방지
  - README 및 릴리즈 노트 전체 업데이트

### Fixed
- GitHub Actions 권한 설정 추가 (릴리즈 생성 실패 해결)

## [1.0.0] - 2026-03-15

### Added
- 🎉 Initial release of DumpCache crawler
- Docker 기반 컨테이너화된 크롤러 시스템
- DC Inside 갤러리 이미지 자동 수집 기능
  - 일반 갤러리 (gall)
  - 마이너 갤러리 (mgallery)
  - 미니 갤러리 (mini)
- 공지사항/광고/설문조사 자동 필터링
  - 클래스 기반 필터링 (동적 공지사항 개수 대응)
  - JavaScript URL 감지 (DC 전체 설문 제외)
- 이미지/영상 포함 게시글만 선택적 수집
- MD5 해시 기반 중복 이미지 검출
- SQLite 데이터베이스를 통한 메타데이터 관리
- 봇 차단 회피 기능
  - 실제 브라우저 User-Agent 사용
  - 요청 간 랜덤 지연 (60초 기본 + 랜덤 분산)
  - HTTP 429 에러 감지 및 지수 백오프
- 환경 변수 기반 설정 (.env)
- Docker Compose v2 지원
- 볼륨 마운트를 통한 데이터 영속성
- 통합 검증 테스트 스크립트 (test_crawler.py)
- 상세한 로그 출력 (INFO/WARNING/ERROR 레벨)

### Features
- **자동화된 수집 사이클**: 설정된 간격으로 자동 반복 실행
- **안전한 크롤링**: Rate limiting 및 랜덤 지연으로 IP 차단 방지
- **데이터 무결성**: 파일 해시 기반 중복 방지
- **유연한 설정**: 환경 변수로 모든 주요 설정 제어 가능
- **백그라운드 실행**: Docker Compose로 데몬 형태 운영
- **데이터 영속성**: 로컬 볼륨 마운트로 데이터 안전 보관

### Configuration
- `GALLERY_URL`: 수집할 갤러리 전체 URL
- `CRAWL_INTERVAL`: 수집 간격 (초 단위, 기본값: 60)
- `IMAGE_SAVE_PATH`: 이미지 저장 경로
- `METADATA_DB_PATH`: 메타데이터 DB 경로
- `MAX_POSTS_PER_CYCLE`: 사이클당 최대 게시글 수 (기본값: 10)
- `DEBUG`: 디버그 모드 활성화 여부

### Technical Details
- Python 3.11 기반
- 주요 의존성:
  - requests 2.31.0
  - beautifulsoup4 4.12.3
  - lxml 5.1.0
  - python-dotenv 1.0.1
  - Pillow 10.2.0
  - pytz 2024.1
- Docker Compose V2 호환
- SQLite3 데이터베이스

### Documentation
- README.md: 사용자 가이드
- CLAUDE.md: 프로젝트 가이드라인 및 개발자 문서
- .env.example: 환경 변수 템플릿
- 인라인 코드 주석 및 docstring

### Deployment
- GitHub Actions 자동 배포 워크플로우
- Docker Hub 멀티 아키텍처 이미지 (amd64, arm64)
- GitHub Release 자동 생성 및 파일 첨부

---

## 🔗 Links

- **GitHub Repository**: https://github.com/igor0670/dumpcache
- **Docker Hub**: https://hub.docker.com/r/igor0670/dumpcache
- **Latest Release**: https://github.com/igor0670/dumpcache/releases/latest

[1.0.1]: https://github.com/igor0670/dumpcache/releases/tag/v1.0.1
[1.0.0]: https://github.com/igor0670/dumpcache/releases/tag/v1.0.0
