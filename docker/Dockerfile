FROM opendatacube/datacube-core:1.7

ENV CURL_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"

WORKDIR /Datacube/S3_scripts

RUN apt-get update
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN apt-get install ca-certificates
RUN echo "\nexport CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt" >> ~/.profile
RUN . ~/.profile

RUN apt-get install wget

COPY Landsat/ Landsat/

COPY docker/entrypoint.sh ./entrypoint.sh
RUN chmod 744 entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["tail -f /dev/null"]
