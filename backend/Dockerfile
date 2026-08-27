# Backend image: FastAPI app served by uvicorn.
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer separately
# from application code -- rebuilds are fast unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# In production, migrations should be run as a separate step (see
# docker-compose.yml's backend command), not baked into the image start.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
