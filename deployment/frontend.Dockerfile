FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit

COPY frontend ./frontend

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0"]

