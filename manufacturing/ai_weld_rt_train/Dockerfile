# 1. Use a clean, lightweight Python base
FROM python:3.11-slim

# 2. Install essential graphics rendering dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Establish the operational working directory
WORKDIR /app

# 4. Copy ONLY the requirements file first (Crucial for Docker caching)
COPY requirements.txt .

# 5. FORCE the lightweight, CPU-specific PyTorch framework to avoid the 3GB bloat
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 6. Install the remaining engineering dependencies (Streamlit, Ultralytics, OpenCV, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy your source code over (This layer builds instantly!)
COPY . .

# 8. Set up your local execution folder infrastructure
RUN mkdir -p logs data/raw data/processed data/reports

# 9. Expose Streamlit's native port
EXPOSE 8501

# 10. Start up the app using an absolute, stable port value
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]