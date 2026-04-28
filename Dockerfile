# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose ports
EXPOSE 8000  
# FastAPI
EXPOSE 8501  
# Streamlit

# Environment variables
ENV OPENAI_API_KEY=""
ENV LLMOPS_LOG_FILE="llmops_logs.jsonl"

# Start both backend and frontend
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 & streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]
