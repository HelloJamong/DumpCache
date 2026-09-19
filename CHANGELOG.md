# Changelog

> 버전 형식: `YY.메이저.마이너` (연도 두 자리 · 기능 추가 시 메이저 · 버그/내부 수정 시 마이너).
> 태그명은 버전과 동일하며 `v` 접두사를 붙이지 않는다.

## [26.2.1] - 2026-09-19

### Added
- HTTP 응답 진단 로그 추가
  - 요청 종류, 재시도 횟수, 상태 코드, 응답 시간·크기, Content-Type, 서버, Retry-After 기록
  - 리다이렉트 횟수, 최종 URL, 응답 본문 SHA-256 축약 해시 기록
  - `403`, `429`, 빈 응답, 소형 HTML, 일반적인 접근 제한 문구 탐지
  - 토큰 등 민감한 URL 쿼리 값 자동 마스킹
- `HTTP_DIAGNOSTICS` 환경 변수 추가 (기본값 `True`)
- HTTP 진단 로그·재시도·차단 탐지 회귀 테스트 추가

### Changed
- HTTP 오류와 재시도 성공 결과를 일관된 형식으로 기록하도록 요청 로그 개선
- 갤러리 목록 파싱 실패 시 응답 진단 정보와 차단 의심 지표를 함께 기록
- `DEBUG=True` 설정 시 디버그 로그 레벨이 실제로 적용되도록 수정

## [26.2.0] - 2026-08-29

### Added
- 새 게시글만 수집 (이미 처리한 게시글 자동 건너뛰기)
  - `processed_posts` 테이블에 `(갤러리 ID, 게시글 ID)` 단위로 처리 이력 기록
  - 매 사이클 목록을 다시 훑되 신규 게시글만 다운로드 → 요청량·중복 처리 감소
  - `MAX_POSTS_PER_CYCLE`은 이제 "사이클당 새 게시글 수" 기준
  - 게시글 페이지 로딩 실패 시에는 기록하지 않고 다음 사이클에 재시도
- 멀티 갤러리 모드 (최대 3개 동시 수집)
  - `MULTI_MODE` (기본 `False`), `MULTI_GALLERY_COUNT` (`2` 또는 `3`)
  - 갤러리 주소는 `GALLERY_URL`(1번) + `GALLERY_URL_2` + `GALLERY_URL_3`
  - 갤러리 간 랜덤 지연 추가
- 이미지를 `images/<갤러리명>/` 하위 폴더에 갤러리별로 분리 저장 (단일·멀티 공통)
  - 갤러리명은 목록 페이지에서 추출, 실패 시 갤러리 ID로 대체

### Changed
- `test_crawler.py`가 설정된 모든 갤러리를 순회하며 검증

## [26.1.0] - 2026-08-29

### Added
- 컨테이너를 비루트 사용자(uid 1000)로 실행
- `SIGTERM`/`SIGINT` 처리 — `docker compose down` 시 진행 중인 사이클만 마치고 안전하게 종료
  - `docker-compose.yml`에 `stop_grace_period: 30s` 추가

### Changed
- 버전 체계를 `YY.메이저.마이너` 형식으로 전환
  - git 태그에서 `v` 접두사 제거 (`v1.0.2` → `26.1.0`)
  - 릴리즈 워크플로우 태그 트리거·버전 추출 로직 수정
  - README 버전 예시 및 이미지 pull 명령 갱신
- 미사용 의존성 제거: `lxml`, `Pillow`, `pytz`
  - HTML 파싱은 표준 `html.parser`, DB는 내장 `sqlite3` 사용
  - Dockerfile에서 불필요한 `gcc` 빌드 패키지 설치 제거 (이미지 크기 축소)
- `test_crawler.py`가 `crawler.py`의 헤더·필터 로직을 재사용하도록 변경 (중복 코드 제거)
- README 환경 변수 예시를 placeholder로 교체 (특정 갤러리 ID 노출 제거)
- 릴리즈 워크플로우 액션 버전 상향: `docker/build-push-action@v5→v6`, `softprops/action-gh-release@v1→v2`

### Fixed
- 첨부 이미지가 없거나 전부 중복인 정상 게시글을 크롤링 에러로 집계하던 문제 수정
- 이미지 URL의 쿼리 파라미터(`&...`)가 저장 파일명에 포함될 수 있던 문제 수정
- 릴리즈 노트 추출 `awk` 스크립트가 빈 문자열을 반환하던 문제 수정

## [1.0.2] - 2026-03-15

### Changed
- GitHub 저장소 주소 업데이트: `igor0670/dumpcache` → `HelloJamong/DumpCache`
  - README, CHANGELOG, 워크플로우 전체 URL 변경
  - Docker Hub는 `igor0670/dumpcache` 유지
- Docker Compose v1/v2 호환성 개선
  - `version: '3.8'` 명시로 v1 환경(Synology NAS 등) 지원
  - README에 v1/v2 명령어 옵션 추가
  - docker-compose.yml에 호환성 안내 주석 추가

### Removed
- `docker-compose.dev.yml` 제거
  - 단일 `docker-compose.yml`로 통합 (Docker Hub 이미지 사용)
  - 로컬 개발은 `docker build` 명령어 사용으로 단순화

## [1.0.1] - 2026-03-15

### Changed
- 환경 변수 예시 파일명 변경: `.env.example` → `default.env.example`
  - 더 명확한 파일명으로 사용자 혼동 방지
  - README 및 릴리즈 노트 전체 업데이트
- Docker Compose 설정 단순화
  - `docker-compose.yml`: Docker Hub 이미지 사용 (즉시 실행 가능)
  - 개발자는 `docker build` 명령어로 로컬 빌드 가능
  - GitHub Release 다운로드 시 즉시 실행 가능

### Fixed
- GitHub Actions 권한 설정 추가 (릴리즈 생성 실패 해결)
- GitHub Release로 설치 시 Dockerfile 없어서 빌드 실패하는 문제 해결

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

- **GitHub Repository**: https://github.com/HelloJamong/DumpCache
- **Docker Hub**: https://hub.docker.com/r/igor0670/dumpcache
- **Latest Release**: https://github.com/HelloJamong/DumpCache/releases/latest

[26.2.0]: https://github.com/HelloJamong/DumpCache/releases/tag/26.2.0
[26.1.0]: https://github.com/HelloJamong/DumpCache/releases/tag/26.1.0
[1.0.2]: https://github.com/HelloJamong/DumpCache/releases/tag/v1.0.2
[1.0.1]: https://github.com/HelloJamong/DumpCache/releases/tag/v1.0.1
[1.0.0]: https://github.com/HelloJamong/DumpCache/releases/tag/v1.0.0
