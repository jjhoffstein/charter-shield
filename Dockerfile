FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY skyprice/ skyprice/
COPY data/ data/
COPY config.toml .
RUN pip install --upgrade pip && pip install -e .
EXPOSE 8000
CMD ["uvicorn", "skyprice.api:app", "--host", "0.0.0.0", "--port", "8000"]
