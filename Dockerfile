FROM python:3.8

# To get output of print statements on console
ENV PYTHONUNBUFFERED 0

# Setting up API
WORKDIR /api

COPY requirements.txt .

# Installing API dependencies other than object detection API and Tensorflow
RUN pip install --upgrade pip && pip install --trusted-host pypi.python.org --use-deprecated=legacy-resolver -r requirements.txt

COPY api .

# Testing code before spinning up the API
# WORKDIR /tests

# COPY tests .

# RUN pytest

# WORKDIR /api

# RUN rm -rf ../tests

ENV PORT="${PORT:-7070}"

# Docker entrypoint
CMD gunicorn main:app --bind 0.0.0.0:$PORT --workers=4 -k uvicorn.workers.UvicornWorker