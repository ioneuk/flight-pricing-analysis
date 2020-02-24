FROM lambci/lambda:python3.6
LABEL maintainer="tech@21buttons.com"

USER root

ENV APP_DIR /var/task

WORKDIR $APP_DIR

COPY requirements.txt .
COPY ./scrapper/bin ./bin
COPY ./scrapper/lib/python3.6/site-packages/ ./lib

RUN mkdir -p $APP_DIR/lib
RUN pip3 install -r requirements.txt -t /var/task/lib