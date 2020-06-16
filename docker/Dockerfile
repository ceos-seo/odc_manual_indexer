FROM opendatacube/datacube-core:1.7

ENV CURL_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"

RUN apt-get update
RUN pip install awscli
RUN pip install boto3 ruamel.yaml
RUN apt-get install ca-certificates
#RUN apt-get install nano

#RUN echo -e "\nexport CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt" >> ~/.profile
#RUN source ~/.profile
RUN apt-get install wget
RUN wget https://raw.githubusercontent.com/opendatacube/datacube-dataset-config/master/scripts/index_from_s3_bucket.py
RUN mkdir -p $HOME/Datacube/S3_scripts
WORKDIR $HOME/Datacube/S3_scripts

COPY Landsat/ Landsat/

CMD ["bash"]
