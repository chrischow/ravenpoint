FROM  continuumio/miniconda3

# FROM python:3-alpine3.10

WORKDIR /usr/src

COPY . .

EXPOSE 5000


RUN pip install odata-query flask-smorest-sqlalchemy-odata Werkzeug==2.1.2 Flask==2.1.2 flask-restx==0.5.1


RUN conda config --append channels conda-forge  &&\ 
conda config --append channels anaconda &&\ 
conda create --name ravenpoint &&\
conda install -y -c conda-forge --file conda-requirements.txt
# RUN conda config --append channels anaconda 

# RUN conda create --name ravenpoint 

# RUN conda install -y -c conda-forge --file conda-requirements.txt


# RUN conda activate ravenpoint

SHELL ["conda", "run", "-n", "ravenpoint", "/bin/bash", "-c"]

RUN flask db init && \
flask db migrate -m "Initial migration" &&\
flask db upgrade

# RUN pip install --upgrade pip

# RUN pip install -r requirements.txt



CMD ["python", "app.py"]




