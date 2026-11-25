FROM python:3.13-slim AS build
WORKDIR /app
COPY requirements.lock.txt .
RUN pip install --prefix=/install --no-cache-dir --require-hashes -r requirements.lock.txt

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --from=build /install /usr/local
COPY app ./app
RUN useradd -m saansplan && chown -R saansplan:saansplan /app
USER saansplan
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c 'import urllib.request, sys; sys.exit(0 if urllib.request.urlopen("http://127.0.0.1:10000/health").getcode() == 200 else 1)'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
