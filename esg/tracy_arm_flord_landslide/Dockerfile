# ---------------------------------------------------------
# Base Image
# ---------------------------------------------------------
FROM python:3.11-slim

# ---------------------------------------------------------
# System Dependencies (GDAL, GEOS, PROJ, etc.)
# Required for rasterio, geopandas, shapely
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV GDAL_DATA=/usr/share/gdal
ENV PROJ_LIB=/usr/share/proj

# ---------------------------------------------------------
# Create working directory
# ---------------------------------------------------------
WORKDIR /app

# ---------------------------------------------------------
# Copy project files
# ---------------------------------------------------------
COPY requirements.txt .
COPY setup.py .
COPY pyproject.toml .
COPY src ./src
COPY app ./app
COPY data ./data

# ---------------------------------------------------------
# Install Python dependencies
# ---------------------------------------------------------
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ---------------------------------------------------------
# Expose Streamlit port
# ---------------------------------------------------------
EXPOSE 8501

# ---------------------------------------------------------
# Streamlit configuration (no browser, external access)
# ---------------------------------------------------------
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV STREAMLIT_SERVER_ENABLEXSRSFPROTECTION=false

# ---------------------------------------------------------
# Default command: run the Streamlit app
# ---------------------------------------------------------
CMD ["streamlit", "run", "app/main.py"]
