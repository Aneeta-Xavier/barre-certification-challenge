FROM python:3.11-slim

WORKDIR /app

# System deps for PyMuPDF / faiss wheels are already bundled; keep image lean.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render/HF Spaces inject $PORT; default to 8000 locally.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "chainlit run app.py --host 0.0.0.0 --port ${PORT}"]
