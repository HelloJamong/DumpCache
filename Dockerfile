# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 복사
COPY crawler.py .
COPY setup.py .

# data 디렉토리 생성
RUN mkdir -p /app/data/images

# 환경 변수 설정 (기본값)
ENV PYTHONUNBUFFERED=1

# 크롤러 실행
CMD ["python", "crawler.py"]
