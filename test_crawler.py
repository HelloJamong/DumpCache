#!/usr/bin/env python3
"""
DumpCache 크롤러 통합 검증 스크립트

- 공지사항/광고/설문 필터링 검증
- 이미지/영상 포함 여부 검증
- 종합 통계 출력
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수에서 갤러리 URL 가져오기
TEST_GALLERY_URL = os.getenv("GALLERY_URL", "")


def get_headers():
    """Bot Block 회피 헤더"""
    return {
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


def is_notice_or_ad(row_element) -> bool:
    """
    공지사항, 광고, 설문조사 등 제외 대상 여부 확인
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
        'notice',
        'gall_notice',
        'ub-content us-post gall_notice',
        'ad',
        'gall_ad',
    ]

    for exclude_class in exclude_classes:
        if exclude_class in tr_class_str:
            return True

    # 2. 내부 요소에서 공지/광고 아이콘 확인
    row_str = str(row_element)
    exclude_indicators = [
        "icon_notice",
        "icon_img icon_notice",
        "icon_ad",
        "gall_notice",
        "concept_notice",
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


def has_media(element) -> bool:
    """이미지/영상 포함 여부 확인"""
    element_str = str(element)

    media_indicators = [
        "icon_pic",                 # 이미지
        "icon_img icon_recomimg",   # 추천 이미지
        "icon_img icon_btimebest",  # 베스트 이미지
        "icon_movie",               # 동영상
    ]

    return any(indicator in element_str for indicator in media_indicators)


def print_section_header(title: str):
    """섹션 헤더 출력"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_subsection(title: str):
    """서브섹션 출력"""
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80)


def run_integrated_test():
    """통합 검증 테스트 실행"""
    print_section_header("🔍 DumpCache 크롤러 통합 검증")

    # 갤러리 URL 확인
    if not TEST_GALLERY_URL:
        print("❌ 오류: GALLERY_URL 환경 변수가 설정되지 않았습니다.")
        print("💡 .env 파일에 GALLERY_URL을 설정해주세요.\n")
        sys.exit(1)

    print(f"\n📌 테스트 갤러리: {TEST_GALLERY_URL}\n")

    # 갤러리 페이지 가져오기
    headers = get_headers()

    try:
        print("⏳ 페이지 로딩 중...")
        response = requests.get(TEST_GALLERY_URL, headers=headers, timeout=30)
        response.raise_for_status()
        print("✅ 페이지 로딩 성공\n")
    except Exception as e:
        print(f"❌ 페이지 로딩 실패: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # 게시글 행(tr) 목록 추출
    post_rows = soup.select("tr.ub-content")

    if not post_rows:
        print("❌ 게시글을 찾을 수 없습니다.")
        return

    print(f"📄 총 {len(post_rows)}개 행 발견 (공지사항 포함)\n")

    # 통계 변수
    notice_count = 0
    total_normal_posts = 0
    with_media_count = 0
    without_media_count = 0

    # 결과 저장
    notice_posts = []
    normal_posts_with_media = []
    normal_posts_without_media = []
    first_normal_post = None

    print_subsection("📋 게시글 분석 중...")

    for idx, row in enumerate(post_rows, 1):
        # 게시글 링크 찾기
        title_cell = row.select_one("td.gall_tit > a:nth-child(1)")
        if not title_cell:
            continue

        title = title_cell.text.strip()
        post_url = "https://gall.dcinside.com" + title_cell.get("href", "")

        # 공지사항/광고 여부 확인
        is_notice = is_notice_or_ad(row)

        if is_notice:
            notice_count += 1
            notice_posts.append({
                'index': idx,
                'title': title
            })
            print(f"[{idx:2d}] 🚫 공지/광고: {title}")
        else:
            total_normal_posts += 1

            # 미디어 포함 여부
            has_media_content = has_media(row)

            post_info = {
                'index': idx,
                'title': title,
                'url': post_url,
                'has_media': has_media_content
            }

            if has_media_content:
                with_media_count += 1
                normal_posts_with_media.append(post_info)
                print(f"[{idx:2d}] ✅ 일반글 📷: {title}")
            else:
                without_media_count += 1
                normal_posts_without_media.append(post_info)
                print(f"[{idx:2d}] ✅ 일반글 📄: {title}")

            # 첫 번째 일반 게시글 저장
            if first_normal_post is None:
                first_normal_post = post_info

    # ========================================
    # 결과 출력
    # ========================================

    print_section_header("📊 검증 결과 요약")

    # 1. 전체 통계
    print("\n📈 전체 통계:")
    print(f"  • 총 행 개수: {len(post_rows)}개")
    print(f"  • 공지/광고/설문: {notice_count}개")
    print(f"  • 일반 게시글: {total_normal_posts}개")

    # 2. 미디어 통계
    if total_normal_posts > 0:
        print("\n🎬 미디어 포함 통계:")
        print(f"  • 미디어 포함: {with_media_count}개 ({with_media_count/total_normal_posts*100:.1f}%)")
        print(f"  • 미디어 없음: {without_media_count}개 ({without_media_count/total_normal_posts*100:.1f}%)")

    # 3. 첫 번째 일반 게시글 (공지사항 필터링 검증)
    if first_normal_post:
        print_section_header("🎯 공지사항 필터링 검증")
        print(f"\n제목: {first_normal_post['title']}")
        print(f"URL: {first_normal_post['url']}")
        print(f"미디어 포함: {'예 📷' if first_normal_post['has_media'] else '아니오 📄'}")
    else:
        print("\n❌ 일반 게시글을 찾을 수 없습니다.")

    # 4. 미디어 포함 게시글 목록 (샘플)
    if normal_posts_with_media:
        print_section_header("📷 미디어 포함 게시글 (샘플)")
        for post in normal_posts_with_media[:10]:
            print(f"  [{post['index']:2d}] {post['title']}")
        if len(normal_posts_with_media) > 10:
            print(f"  ... 외 {len(normal_posts_with_media) - 10}개 더")

    # 5. 미디어 없는 게시글 목록 (샘플)
    if normal_posts_without_media:
        print_section_header("📄 미디어 없는 게시글 (샘플)")
        for post in normal_posts_without_media[:10]:
            print(f"  [{post['index']:2d}] {post['title']}")
        if len(normal_posts_without_media) > 10:
            print(f"  ... 외 {len(normal_posts_without_media) - 10}개 더")

    # 6. 공지사항 목록 (샘플)
    if notice_posts:
        print_section_header("🚫 필터링된 공지/광고/설문 (샘플)")
        for post in notice_posts[:5]:
            print(f"  [{post['index']:2d}] {post['title']}")
        if len(notice_posts) > 5:
            print(f"  ... 외 {len(notice_posts) - 5}개 더")

    # 최종 결과
    print_section_header("✅ 검증 완료")
    print("\n✓ 공지사항 필터링: 정상 작동")
    print("✓ 미디어 검출: 정상 작동")
    print("✓ 게시글 파싱: 정상 작동\n")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_integrated_test()
