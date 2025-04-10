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

WORKDIR /cogu-app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "coguMSHP.wsgi:application", "--bind=0.0.0.0:8000", "--workers=4", "--timeout=180"]

#FROM python:3.9-slim
#LABEL authors="ogahserge"
#
#WORKDIR /cogu-app
#ENV VIRTUAL_ENV=/opt/venv
#RUN python3 -m venv $VIRTUAL_ENV
#ENV PATH="$VIRTUAL_ENV/bin:$PATH"
#
## Upgrade pip
#RUN pip install --upgrade pip
#
## Install system dependencies including g++ and GDAL
#RUN apt-get update && \
#    apt-get install -y --no-install-recommends \
#    g++ \
#    gcc \
#    gdal-bin \
#    libgdal-dev \
#    libgeos-dev \
#    libpq-dev \
#    software-properties-common \
#    ca-certificates \
#    dirmngr \
#    gnupg2 \
#    lsb-release \
#    postgresql-client && \
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists/*
#
## Set GDAL environment variables
#ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
#ENV C_INCLUDE_PATH=/usr/include/gdal
#ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
#
## Copy the requirements.txt and install Python dependencies
#COPY requirements.txt /cogu-app/requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt
#
## Copy the rest of the application
#COPY . /cogu-app/
#
## Expose port 8000
#EXPOSE 8000
#
## Start the application using Gunicorn
#CMD ["gunicorn", "coguMSHP.wsgi:application", "--bind=0.0.0.0:8000", "--workers=4", "--timeout=180", "--log-level=debug"]
#
