
FROM python:3.11-slim

EXPOSE 8080
WORKDIR /app


ENV XDG_CACHE_HOME=/tmp
ENV YFINANCE_CACHE_DIR=/tmp
ENV NUMBA_CACHE_DIR=/tmp
ENV MPLCONFIGDIR=/tmp
ENV HOME=/tmp

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["streamlit", "run", "src/dashboard.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
