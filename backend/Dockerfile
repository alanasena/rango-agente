# Imagem da API do Rangô (Python + FastAPI)
FROM python:3.12-slim

# Mostra os logs na hora e não cria arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala as bibliotecas primeiro (o Docker reaproveita essa etapa se nada mudou)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY avaliacao ./avaliacao
COPY tests ./tests
COPY pytest.ini .

# Roda com um usuário comum, não como administrador (mais seguro)
RUN useradd --create-home rango && chown -R rango /app
USER rango

EXPOSE 8000
# PORT existe para serviços de hospedagem que escolhem a porta sozinhos
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
