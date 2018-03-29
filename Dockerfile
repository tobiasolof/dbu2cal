FROM python:3.6.4

WORKDIR /

COPY requirements.txt ./
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . ./dbu2cal
WORKDIR /dbu2cal

ENV FLASK_APP=app.py

EXPOSE 5000

ENTRYPOINT ["python"]
CMD ["app.py"]
