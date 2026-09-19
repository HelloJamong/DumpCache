#!/usr/bin/env python3
"""HTTP 진단 로그와 차단 의심 응답 탐지 회귀 테스트."""

import unittest
from datetime import timedelta
from unittest.mock import patch

import requests

from crawler import BotBlockBypass, Config, _stop_event


def make_response(
    status: int,
    body: bytes,
    *,
    url: str = "https://example.invalid/gallery?id=test",
    content_type: str = "text/html; charset=utf-8",
) -> requests.Response:
    """네트워크 없이 requests.Response 테스트 객체를 생성한다."""
    response = requests.Response()
    response.status_code = status
    response._content = body
    response.url = url
    response.headers.update({
        "Content-Type": content_type,
        "Server": "test-edge",
    })
    response.elapsed = timedelta(milliseconds=123)
    response.history = []
    return response


class RequestDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        _stop_event.clear()
        self.original_http_diagnostics = Config.HTTP_DIAGNOSTICS
        Config.HTTP_DIAGNOSTICS = True

    def tearDown(self):
        Config.HTTP_DIAGNOSTICS = self.original_http_diagnostics
        _stop_event.clear()

    @patch("crawler.requests.get")
    def test_success_log_contains_response_metadata(self, mock_get):
        body = b"<html><title>Gallery</title><body>" + (b"x" * 4096) + b"</body></html>"
        mock_get.return_value = make_response(
            200,
            body,
        )

        with self.assertLogs("crawler", level="INFO") as logs:
            response = BotBlockBypass.safe_request(
                "https://example.invalid/gallery?id=test",
                {"User-Agent": "test"},
                request_kind="gallery-list",
            )

        self.assertEqual(response.status_code, 200)
        output = "\n".join(logs.output)
        self.assertIn("HTTP 응답", output)
        self.assertIn("kind=gallery-list", output)
        self.assertIn("status=200", output)
        self.assertIn(f"bytes={len(body)}", output)
        self.assertIn("content_type=text/html; charset=utf-8", output)
        self.assertIn("server=test-edge", output)
        self.assertIn("body_sha256=", output)

    @patch("crawler._stop_event.wait", return_value=False)
    @patch("crawler.requests.get")
    def test_retry_success_is_recorded(self, mock_get, _mock_wait):
        limited = make_response(429, b"rate limited")
        limited.headers["Retry-After"] = "120"
        success = make_response(
            200,
            b"<html><body>" + (b"x" * 4096) + b"</body></html>",
        )
        mock_get.side_effect = [limited, success]

        with self.assertLogs("crawler", level="INFO") as logs:
            response = BotBlockBypass.safe_request(
                "https://example.invalid/gallery?id=test",
                {"User-Agent": "test"},
                request_kind="gallery-list",
            )

        self.assertEqual(response.status_code, 200)
        output = "\n".join(logs.output)
        self.assertIn("HTTP 429 감지", output)
        self.assertIn("retry_after=120", output)
        self.assertIn("HTTP 재시도 성공", output)
        self.assertIn("attempt=2/3", output)

    @patch("crawler._stop_event.wait", return_value=False)
    @patch("crawler.requests.get")
    def test_forbidden_response_is_logged_as_block_suspected(self, mock_get, _mock_wait):
        forbidden = make_response(403, b"<html><body>Access Denied</body></html>")
        success = make_response(
            200,
            b"<html><body>" + (b"x" * 4096) + b"</body></html>",
        )
        mock_get.side_effect = [forbidden, success]

        with self.assertLogs("crawler", level="INFO") as logs:
            response = BotBlockBypass.safe_request(
                "https://example.invalid/gallery?id=test",
                {"User-Agent": "test"},
                request_kind="gallery-list",
            )

        self.assertEqual(response.status_code, 200)
        output = "\n".join(logs.output)
        self.assertIn("HTTP 차단 의심 응답", output)
        self.assertIn("status=403", output)
        self.assertIn("indicators=http-403,small-html,access-denied", output)
        self.assertIn("HTTP 재시도 성공", output)

    @patch("crawler._stop_event.wait", return_value=False)
    @patch("crawler.requests.get")
    def test_server_error_is_not_mislabeled_as_block(self, mock_get, _mock_wait):
        server_error = make_response(500, b"<html><body>temporary error</body></html>")
        success = make_response(
            200,
            b"<html><body>" + (b"x" * 4096) + b"</body></html>",
        )
        mock_get.side_effect = [server_error, success]

        with self.assertLogs("crawler", level="INFO") as logs:
            BotBlockBypass.safe_request(
                "https://example.invalid/gallery?id=test",
                {"User-Agent": "test"},
                request_kind="gallery-list",
            )

        output = "\n".join(logs.output)
        self.assertIn("HTTP 오류 응답", output)
        self.assertIn("status=500", output)

    def test_sensitive_query_values_are_redacted(self):
        safe_url = BotBlockBypass._safe_url(
            "https://example.invalid/gallery?id=test&token=secret-value&api_key=private"
        )

        self.assertIn("id=test", safe_url)
        self.assertNotIn("secret-value", safe_url)
        self.assertNotIn("private", safe_url)
        self.assertIn("redacted", safe_url)

    def test_block_indicators_detect_small_challenge_html(self):
        response = make_response(
            200,
            "<html><title>Access Denied</title><body>비정상적인 접근입니다.</body></html>".encode(),
        )

        indicators = BotBlockBypass.get_block_indicators(response)

        self.assertIn("small-html", indicators)
        self.assertIn("access-denied", indicators)
        self.assertIn("abnormal-access", indicators)

    def test_normal_gallery_html_has_no_block_indicator(self):
        body = (
            "<html><title>Normal</title><body>"
            + "<tr class='ub-content'></tr>" * 50
            + "x" * 4096
            + "</body></html>"
        ).encode()
        response = make_response(200, body)

        indicators = BotBlockBypass.get_block_indicators(response)

        self.assertEqual(indicators, [])


if __name__ == "__main__":
    unittest.main()
