FROM python:3.9-slim
LABEL authors="ogahserge"

WORKDIR /rage-app
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip

# Install system dependencies including g++ and GDAL
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    g++ \
    gcc \
    gdal-bin \
    libgdal-dev \
    libpq-dev \
    software-properties-common \
    ca-certificates \
    dirmngr \
    gnupg2 \
    lsb-release \
    postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so

# Copy the requirements.txt and install Python dependencies
COPY requirements.txt /rage-app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /rage-app/

# Expose port 8000
EXPOSE 8000

# Start the application using Gunicorn
CMD ["gunicorn", "rage_INHP.wsgi:application", "--bind=0.0.0.0:8000", "--workers=4", "--timeout=180", "--log-level=debug"]

