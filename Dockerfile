# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 복사
COPY crawler.py .
COPY test_crawler.py .
COPY test_request_diagnostics.py .

# 비루트 사용자 생성 (uid 1000) 및 data 디렉토리 소유권 부여
# 볼륨 마운트 시 호스트의 data 디렉토리도 uid 1000이 쓸 수 있어야 함
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /app/data/images \
    && chown -R app:app /app

# 환경 변수 설정 (기본값)
ENV PYTHONUNBUFFERED=1

USER app

# 크롤러 실행
CMD ["python", "crawler.py"]
