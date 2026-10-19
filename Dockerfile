ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 先安装依赖，让仅修改应用代码时可以复用依赖层缓存。
COPY requirements.txt ./

ARG PIP_INDEX_URL=
RUN if [ -n "$PIP_INDEX_URL" ]; then \
        python -m pip install --no-cache-dir \
        --index-url "$PIP_INDEX_URL" -r requirements.txt; \
    else \
        python -m pip install --no-cache-dir -r requirements.txt; \
    fi

# 同时包含应用代码、静态网页和已导出的模型。
COPY app/ ./app/

# 使用普通用户运行服务。
RUN useradd --create-home --uid 10001 appuser
USER 10001

ARG APP_ENV=production
ARG MODEL_VERSION=6

ENV APP_ENV=${APP_ENV} \
    MODEL_VERSION=${MODEL_VERSION}

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]