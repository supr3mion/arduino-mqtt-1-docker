# install python
FROM python:3.11.0

# create working directory
RUN mkdir /usr/src/app
WORKDIR /usr/src/app

# copy nececary files into working directory
COPY ./python/requirements.txt .
COPY ./python/main.py .

# update pip and install python requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# start python script
CMD [ "python", "main.py" ]