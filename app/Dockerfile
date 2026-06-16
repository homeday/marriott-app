FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.9.20-slim   

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --uid 10001 appuser

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

USER appuser

EXPOSE 8080

CMD ["python", "app.py"]