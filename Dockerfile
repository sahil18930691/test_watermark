FROM python:3.9

# To get output of print statements on console
ENV PYTHONUNBUFFERED 0

# Installing tensorflow and cython
RUN pip install --ignore-installed --upgrade tensorflow==2.5.0 Cython==0.29.23 && python -c "import tensorflow as tf;print(tf.reduce_sum(tf.random.normal([1000, 1000])))"

# Installing other dependencies to setup the container for object detection API
RUN apt-get update && \
    apt-get install -y unzip \
    protobuf-compiler \
    python-pil \
    python-lxml \
    python-tk \
    libgl1-mesa-dev

# Extraction of cached TF models
WORKDIR /Tensorflow 

COPY models.zip .

RUN unzip models.zip && mv models-master models && rm models.zip

WORKDIR /

# Setting up protobuf
RUN curl -OL "https://github.com/google/protobuf/releases/download/v3.0.0/protoc-3.0.0-linux-x86_64.zip" && \
    unzip protoc-3.0.0-linux-x86_64.zip -d proto3 && \
    mv proto3/bin/* /usr/local/bin && \
    mv proto3/include/* /usr/local/include && \
    rm -rf proto3 protoc-3.0.0-linux-x86_64.zip

RUN cd /Tensorflow/models/research && \
    protoc object_detection/protos/*.proto --python_out=.

# Installing coco API to avoid errors
RUN git clone https://github.com/cocodataset/cocoapi.git

WORKDIR /cocoapi/PythonAPI

RUN make

WORKDIR /

RUN cp -r /cocoapi/PythonAPI/pycocotools /Tensorflow/models/research/

RUN rm -rf cocoapi

# Installing Object Detection API
WORKDIR /Tensorflow/models/research

RUN cp object_detection/packages/tf2/setup.py .

RUN python -m pip install --use-feature=2020-resolver . && python object_detection/builders/model_builder_tf2_test.py

WORKDIR /

RUN rm -rf Tensorflow

# Setting up API
WORKDIR /api

COPY requirements.txt .

# Installing API dependencies other than object detection API and Tensorflow
RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY api .

# Testing code before spinning up the API
WORKDIR /tests

COPY tests .

RUN pytest

WORKDIR /api

RUN rm -rf ../tests

ENV PORT="${PORT:-8080}"

# Docker entrypoint
CMD gunicorn main:app --bind 0.0.0.0:$PORT --timeout 600 -k uvicorn.workers.UvicornWorker
