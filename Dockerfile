FROM python:3.9-slim

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    libpq-dev \
    gcc \
    g++ \
    postgresql-client \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


# Optional: force Django to use the correct GEOS lib
ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# Set GDAL env if needed
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so

ENV PYTHONUNBUFFERED=1
WORKDIR /cogu-app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN mkdir -p /cogu-app/logs

COPY . .

EXPOSE 8000


#CMD ["gunicorn", "coguMSHP.wsgi:application", "--bind=0.0.0.0:8000", "--workers=4", "--timeout=180"]
CMD ["gunicorn", "coguMSHP.wsgi:application", "--bind=0.0.0.0:8000", "--workers=4", "--timeout=180", "--access-logfile=-", "--error-logfile=-", "--capture-output", "--log-level=info"]
