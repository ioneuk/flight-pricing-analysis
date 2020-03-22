FROM python:3.7
EXPOSE 5000
WORKDIR app
COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY ./src /app/src/
COPY ./run_scripts/model.pkl /app/
CMD python -m src.app
