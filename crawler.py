#!/usr/bin/env python3
"""
DumpCache - Community Gallery Image Crawler
"""

import os
import sys
import time
import random
import hashlib
import sqlite3
import logging
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from typing import Tuple, Optional, List, Dict

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 환경 변수 로딩
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Config:
    """환경 변수 기반 설정"""
    GALLERY_URL = os.getenv('GALLERY_URL', '')
    CRAWL_INTERVAL = int(os.getenv('CRAWL_INTERVAL', '60'))
    IMAGE_SAVE_PATH = os.getenv('IMAGE_SAVE_PATH', '/app/data/images')
    METADATA_DB_PATH = os.getenv('METADATA_DB_PATH', '/app/data/metadata.db')
    MAX_POSTS_PER_CYCLE = int(os.getenv('MAX_POSTS_PER_CYCLE', '10'))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    @classmethod
    def validate(cls):
        """필수 설정 검증"""
        if not cls.GALLERY_URL or cls.GALLERY_URL == '갤러리 주소 입력':
            logger.error("GALLERY_URL이 설정되지 않았습니다. .env 파일을 확인하세요.")
            sys.exit(1)


class BotBlockBypass:
    """Bot Block 회피를 위한 헤더 및 요청 관리"""

    @staticmethod
    def get_headers(referer: Optional[str] = None) -> Dict[str, str]:
        """
        실제 브라우저처럼 보이는 헤더 생성
        origin_src.py의 헤더 설정을 기반으로 작성
        """
        headers = {
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "sec-ch-ua-mobile": "?0",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        if referer:
            headers["Referer"] = referer

        return headers

    @staticmethod
    def random_delay(base_interval: int = 60, variance: int = 10):
        """
        랜덤 지연으로 패턴 탐지 회피

        Args:
            base_interval: 기본 대기 시간 (초)
            variance: 변동 범위 (초)
        """
        delay = base_interval + random.randint(-variance, variance)
        delay = max(1, delay)  # 최소 1초
        logger.info(f"다음 수집까지 {delay}초 대기...")
        time.sleep(delay)

    @staticmethod
    def safe_request(url: str, headers: Dict[str, str], max_retries: int = 3) -> Optional[requests.Response]:
        """
        재시도 로직이 포함된 안전한 HTTP 요청

        Args:
            url: 요청 URL
            headers: 요청 헤더
            max_retries: 최대 재시도 횟수

        Returns:
            Response 객체 또는 None
        """
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=30)

                # HTTP 429 (Too Many Requests) 감지
                if response.status_code == 429:
                    wait_time = (2 ** attempt) * 60  # 지수 백오프
                    logger.warning(f"HTTP 429 감지. {wait_time}초 대기 후 재시도...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                logger.warning(f"요청 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 5)  # 점진적 대기
                else:
                    logger.error(f"최대 재시도 횟수 초과: {url}")
                    return None

        return None


class GalleryParser:
    """갤러리 URL 파싱 및 정보 추출"""

    @staticmethod
    def parse_url(url: str) -> Tuple[str, str, str]:
        """
        갤러리 URL을 파싱하여 타입, ID, 베이스 URL 추출

        Args:
            url: 갤러리 URL

        Returns:
            (gallery_type, gallery_id, base_url) 튜플

        Raises:
            ValueError: URL 파싱 실패 시
        """
        parsed = urlparse(url)

        # 갤러리 타입 판단
        if '/mgallery/' in parsed.path:
            gallery_type = 'mgallery'
        elif '/mini/' in parsed.path:
            gallery_type = 'mini'
        else:
            gallery_type = 'gall'

        # 갤러리 ID 추출
        query_params = parse_qs(parsed.query)
        gallery_id = query_params.get('id', [''])[0]

        if not gallery_id:
            raise ValueError("갤러리 ID를 찾을 수 없습니다.")

        # 베이스 URL 생성
        if gallery_type == 'mgallery':
            base_url = f"https://gall.dcinside.com/mgallery/board/lists/?id={gallery_id}"
        elif gallery_type == 'mini':
            base_url = f"https://gall.dcinside.com/mini/board/lists/?id={gallery_id}"
        else:
            base_url = f"https://gall.dcinside.com/board/lists/?id={gallery_id}"

        logger.info(f"갤러리 파싱 완료: 타입={gallery_type}, ID={gallery_id}")
        return gallery_type, gallery_id, base_url


class Database:
    """SQLite 데이터베이스 관리"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """데이터베이스 및 테이블 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # images 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_hash TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                original_url TEXT,
                post_url TEXT,
                post_id TEXT,
                downloaded_at TEXT NOT NULL
            )
        ''')

        # crawl_history 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crawled_at TEXT NOT NULL,
                posts_found INTEGER DEFAULT 0,
                images_downloaded INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()
        logger.info(f"데이터베이스 초기화 완료: {self.db_path}")

    def is_duplicate(self, file_hash: str) -> bool:
        """파일 해시로 중복 확인"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM images WHERE file_hash = ?', (file_hash,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def save_image_metadata(self, file_hash: str, file_name: str, file_path: str,
                           file_size: int, original_url: str, post_url: str, post_id: str):
        """이미지 메타데이터 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO images (file_hash, file_name, file_path, file_size,
                                   original_url, post_url, post_id, downloaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_hash, file_name, file_path, file_size, original_url,
                  post_url, post_id, datetime.now().isoformat()))
            conn.commit()
        except sqlite3.IntegrityError:
            logger.debug(f"중복 해시 발견 (저장 생략): {file_hash}")
        finally:
            conn.close()

    def save_crawl_history(self, posts_found: int, images_downloaded: int, errors: int):
        """크롤링 이력 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO crawl_history (crawled_at, posts_found, images_downloaded, errors)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), posts_found, images_downloaded, errors))
        conn.commit()
        conn.close()


class ImageDownloader:
    """이미지 다운로드 및 저장"""

    def __init__(self, save_path: str, db: Database):
        self.save_path = save_path
        self.db = db

        # 저장 디렉토리 생성
        os.makedirs(save_path, exist_ok=True)

    @staticmethod
    def calculate_hash(content: bytes) -> str:
        """파일 내용의 MD5 해시 계산"""
        return hashlib.md5(content).hexdigest()

    def get_unique_filename(self, base_name: str) -> str:
        """중복되지 않는 파일명 생성"""
        file_path = os.path.join(self.save_path, base_name)

        if not os.path.exists(file_path):
            return base_name

        # 파일명 중복 시 -1, -2 등 추가
        name, ext = os.path.splitext(base_name)
        counter = 1

        while True:
            new_name = f"{name}-{counter}{ext}"
            new_path = os.path.join(self.save_path, new_name)
            if not os.path.exists(new_path):
                return new_name
            counter += 1

    def download_image(self, img_url: str, post_url: str, post_id: str, headers: Dict[str, str]) -> bool:
        """
        이미지 다운로드 및 저장

        Args:
            img_url: 이미지 URL
            post_url: 게시글 URL
            post_id: 게시글 ID
            headers: 요청 헤더

        Returns:
            성공 여부
        """
        try:
            # Referer 설정 (중요: Bot Block 회피)
            headers['Referer'] = post_url

            # 이미지 다운로드
            response = BotBlockBypass.safe_request(img_url, headers)
            if not response:
                return False

            content = response.content
            file_hash = self.calculate_hash(content)

            # 중복 확인 (해시 기반)
            if self.db.is_duplicate(file_hash):
                logger.debug(f"중복 이미지 (해시: {file_hash[:8]}...) - 건너뜀")
                return False

            # 파일명 생성 (URL에서 추출)
            if 'no=' in img_url:
                base_name = img_url.split('no=')[-1]
            else:
                base_name = img_url.split('/')[-1].split('?')[0]

            # 확장자가 없으면 추가
            if '.' not in base_name:
                # Content-Type에서 확장자 추정
                content_type = response.headers.get('Content-Type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    base_name += '.jpg'
                elif 'png' in content_type:
                    base_name += '.png'
                elif 'gif' in content_type:
                    base_name += '.gif'
                elif 'webp' in content_type:
                    base_name += '.webp'
                else:
                    base_name += '.jpg'  # 기본값

            # 중복되지 않는 파일명 생성
            file_name = self.get_unique_filename(base_name)
            file_path = os.path.join(self.save_path, file_name)

            # 파일 저장
            with open(file_path, 'wb') as f:
                f.write(content)

            # 메타데이터 저장
            self.db.save_image_metadata(
                file_hash=file_hash,
                file_name=file_name,
                file_path=file_path,
                file_size=len(content),
                original_url=img_url,
                post_url=post_url,
                post_id=post_id
            )

            logger.info(f"이미지 다운로드 완료: {file_name} ({len(content) // 1024}KB)")
            return True

        except Exception as e:
            logger.error(f"이미지 다운로드 실패 ({img_url}): {e}")
            return False


class GalleryCrawler:
    """갤러리 크롤러 메인 클래스"""

    def __init__(self):
        Config.validate()

        self.gallery_type, self.gallery_id, self.base_url = GalleryParser.parse_url(Config.GALLERY_URL)
        self.db = Database(Config.METADATA_DB_PATH)
        self.downloader = ImageDownloader(Config.IMAGE_SAVE_PATH, self.db)

    @staticmethod
    def has_media(element) -> bool:
        """
        게시글에 이미지/영상 포함 여부 확인
        origin_src.py의 image_check 함수 기반

        Args:
            element: BeautifulSoup 엘리먼트

        Returns:
            미디어 포함 여부
        """
        element_str = str(element)

        # 이미지/영상 아이콘 클래스 확인
        media_indicators = [
            "icon_pic",                 # 이미지
            "icon_img icon_recomimg",   # 추천 이미지
            "icon_img icon_btimebest",  # 베스트 이미지
            "icon_movie",               # 동영상
        ]

        return any(indicator in element_str for indicator in media_indicators)

    @staticmethod
    def is_notice_or_ad(row_element) -> bool:
        """
        공지사항, 광고, 설문조사 등 제외 대상 여부 확인 (개선된 버전)

        DC인사이드는 공지사항의 개수가 계속 변하므로,
        인덱스 기반이 아닌 클래스 기반으로 감지합니다.

        Args:
            row_element: 게시글 행(tr) 엘리먼트

        Returns:
            공지/광고/설문조사 여부
        """
        if not row_element:
            return False

        # 1. tr 태그의 class 속성 확인
        tr_classes = row_element.get('class', [])
        if isinstance(tr_classes, list):
            tr_class_str = ' '.join(tr_classes)
        else:
            tr_class_str = str(tr_classes)

        # 공지사항/광고를 나타내는 클래스
        exclude_classes = [
            'notice',           # 공지사항
            'gall_notice',      # 갤러리 공지
            'ub-content us-post gall_notice',  # 갤러리 공지 (전체 클래스)
            'ad',               # 광고
            'gall_ad',          # 갤러리 광고
        ]

        for exclude_class in exclude_classes:
            if exclude_class in tr_class_str:
                return True

        # 2. 내부 요소에서 공지/광고 아이콘 확인
        row_str = str(row_element)
        exclude_indicators = [
            "icon_notice",          # 공지사항 아이콘
            "icon_img icon_notice", # 공지사항 이미지 아이콘
            "icon_ad",              # 광고 아이콘
            "gall_notice",          # 갤러리 공지
            "concept_notice",       # 개념글 공지
        ]

        for indicator in exclude_indicators:
            if indicator in row_str:
                return True

        # 3. 설문조사 및 특수 게시글 확인 (URL이 javascript:인 경우)
        title_cell = row_element.select_one("td.gall_tit > a:nth-child(1)")
        if title_cell:
            href = title_cell.get("href", "")
            if href.startswith("javascript:") or not href or href == "#":
                return True

        return False

    def download_post_images(self, post_url: str, headers: Dict[str, str]) -> int:
        """
        게시글의 첨부 이미지 다운로드 (갤러리 대문 이미지 제외)
        origin_src.py의 image_download 함수 기반

        Args:
            post_url: 게시글 URL
            headers: 요청 헤더

        Returns:
            다운로드한 이미지 수
        """
        try:
            response = BotBlockBypass.safe_request(post_url, headers)
            if not response:
                return 0

            soup = BeautifulSoup(response.text, 'html.parser')

            # 게시글 ID 추출
            post_id = post_url.split('no=')[-1].split('&')[0] if 'no=' in post_url else 'unknown'

            # 첨부 이미지 목록 (갤러리 대문 제외)
            # div.appending_file_box는 본문 첨부 이미지만 포함
            image_elements = soup.select("div.appending_file_box ul li")

            if not image_elements:
                logger.debug(f"첨부 이미지 없음: {post_url}")
                return 0

            download_count = 0
            for li in image_elements:
                img_tag = li.find('a', href=True)
                if not img_tag:
                    continue

                img_url = img_tag['href']

                # 약간의 지연 (이미지 다운로드 간)
                time.sleep(random.uniform(0.5, 2.0))

                if self.downloader.download_image(img_url, post_url, post_id, headers.copy()):
                    download_count += 1

            return download_count

        except Exception as e:
            logger.error(f"게시글 이미지 다운로드 실패 ({post_url}): {e}")
            return 0

    def crawl_once(self) -> Tuple[int, int, int]:
        """
        1회 크롤링 실행

        Returns:
            (발견한 게시글 수, 다운로드한 이미지 수, 에러 수)
        """
        logger.info(f"크롤링 시작: {self.base_url}")

        headers = BotBlockBypass.get_headers()
        response = BotBlockBypass.safe_request(self.base_url, headers)

        if not response:
            logger.error("갤러리 목록 페이지 로딩 실패")
            return 0, 0, 1

        soup = BeautifulSoup(response.text, 'html.parser')

        # 게시글 행(tr) 목록 추출
        post_rows = soup.select("tr.ub-content")

        if not post_rows:
            logger.warning("게시글을 찾을 수 없습니다. 선택자가 변경되었을 수 있습니다.")
            return 0, 0, 1

        posts_found = 0
        images_downloaded = 0
        errors = 0
        processed = 0

        for row in post_rows:
            # 공지사항/광고 제외 (개선된 감지 로직)
            if self.is_notice_or_ad(row):
                logger.debug("공지사항/광고 제외")
                continue

            # 게시글 링크 찾기
            title_cell = row.select_one("td.gall_tit > a:nth-child(1)")
            if not title_cell:
                continue

            # 미디어 포함 여부 확인
            if not self.has_media(row):
                logger.debug("미디어 미포함 게시글 제외")
                continue

            posts_found += 1

            # 게시글 URL
            post_url = "https://gall.dcinside.com" + title_cell.get("href")
            title = title_cell.text.strip()

            logger.info(f"처리 중: {title}")

            # 이미지 다운로드
            try:
                count = self.download_post_images(post_url, headers.copy())
                images_downloaded += count

                if count == 0:
                    errors += 1
            except Exception as e:
                logger.error(f"게시글 처리 실패: {e}")
                errors += 1

            # 처리 완료 카운트
            processed += 1

            # 최대 처리 수 제한
            if processed >= Config.MAX_POSTS_PER_CYCLE:
                logger.info(f"최대 처리 수 도달 ({Config.MAX_POSTS_PER_CYCLE}개)")
                break

            # 게시글 간 랜덤 지연 (Bot Block 회피)
            time.sleep(random.uniform(2.0, 5.0))

        logger.info(f"크롤링 완료: 게시글 {posts_found}개, 이미지 {images_downloaded}개, 에러 {errors}개")
        return posts_found, images_downloaded, errors

    def run(self):
        """크롤러 메인 루프"""
        logger.info("=" * 60)
        logger.info("DumpCache 크롤러 시작")
        logger.info(f"갤러리: {self.gallery_id} ({self.gallery_type})")
        logger.info(f"수집 간격: {Config.CRAWL_INTERVAL}초")
        logger.info(f"저장 경로: {Config.IMAGE_SAVE_PATH}")
        logger.info("=" * 60)

        cycle = 0

        while True:
            cycle += 1
            logger.info(f"\n{'=' * 60}")
            logger.info(f"수집 사이클 #{cycle}")
            logger.info(f"{'=' * 60}")

            try:
                posts_found, images_downloaded, errors = self.crawl_once()

                # 크롤링 이력 저장
                self.db.save_crawl_history(posts_found, images_downloaded, errors)

            except KeyboardInterrupt:
                logger.info("\n사용자에 의해 중지되었습니다.")
                break
            except Exception as e:
                logger.error(f"예상치 못한 오류: {e}", exc_info=True)
                errors += 1

            # 다음 수집까지 대기 (랜덤 지연)
            BotBlockBypass.random_delay(Config.CRAWL_INTERVAL, variance=10)


def main():
    """메인 함수"""
    try:
        crawler = GalleryCrawler()
        crawler.run()
    except Exception as e:
        logger.error(f"크롤러 초기화 실패: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
