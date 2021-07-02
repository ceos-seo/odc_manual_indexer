FROM jcrattzama/datacube-base:odc1.8.3

ARG BUILD_DIR=/build
ENV BUILD_DIR=${BUILD_DIR}
WORKDIR ${BUILD_DIR}

# Install CA certificates (partly for S3 access).
ENV CURL_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
RUN apt-get update && apt-get install ca-certificates -y
RUN echo "export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt" >> ~/.profile

# Install some system utilities like wget and curl.
RUN DEBIAN_FRONTEND=noninteractive apt-get install \
    wget curl unzip -y < /dev/null

# Install the AWS CLI.
RUN curl "https://s3.amazonaws.com/aws-cli/awscli-bundle.zip" -o "awscli-bundle.zip"
RUN unzip awscli-bundle.zip
RUN python3 ./awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws
RUN rm -rf awscli-bundle.zip awscli-bundle awscli-bundle.zip

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Setup the Open Data Cube configuration.
ENV ODC_DB_HOSTNAME \
    ODC_DB_DATABASE \
    ODC_DB_USER \
    ODC_DB_PASSWORD \
    ODC_DB_PORT
COPY build/native/odc_conf.sh native/odc_conf.sh
COPY build/native/entrypoint.sh native/entrypoint.sh
RUN chmod 777 -R ${BUILD_DIR}

ARG WORKDIR
ENV WORKDIR=${WORKDIR}
WORKDIR $WORKDIR
ARG PYTHONPATH=${WORKDIR}
ENV PYTHONPATH=${PYTHONPATH}

# Install ODC-GEE.
COPY odc_gee odc_gee
RUN cd odc_gee; python3 setup.py build && python3 setup.py install

ENV AWS_ACCESS_KEY_ID \
    AWS_SECRET_ACCESS_KEY
ENTRYPOINT ["/build/native/entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]
