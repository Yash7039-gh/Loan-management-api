# ── Base image ──
FROM python:3.11-slim

# ── Metadata ──
LABEL maintainer="Yash Yadav <yashyadav7039@gmail.com>"
LABEL description="Student Loan Management REST API"
LABEL version="1.0.0"

# ── Working directory ──
WORKDIR /app

# ── Install dependencies ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy source ──
COPY . .

# ── Expose port ──
EXPOSE 5000

# ── Run with gunicorn (production) ──
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]
