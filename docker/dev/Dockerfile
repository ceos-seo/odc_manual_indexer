FROM jcrattzama/datacube-base:odc1.8.3
# jcrattzama/cube-in-a-box:odc1.8.3
# jcrattzama/datacube-core:1.8.3_v2
# jcrattzama/datacube-core:1.7

# Build Tools #
# RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
#         python3-setuptools && \
#     rm -rf /var/lib/apt/lists/*
# RUN pip3 install --upgrade Cython

# End Build Tools #

# Handle Rasterio Issues #

# (Option 1) If using binary rasterio package, to support HTTPS, symlink SSL certs path.
# Note that installing with `pip install --no-binary=rasterio rasterio`
# may not require this, but this is still a good safeguard to use.
# RUN mkdir -p /etc/pki/tls/certs && \
    # ln -s /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt

# (Option 2) Install rasterio from binary.
# RUN pip3 install --no-binary=rasterio rasterio==1.1.8

# End Handle Rasterio Issues #

ENV CURL_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"

WORKDIR /build

# Install CA certificates (partly for S3 access).
RUN apt-get update && apt-get install ca-certificates -y
RUN echo "export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt" >> ~/.profile
# Source the ~/.profile file.
RUN . ~/.profile

# Install some system utilities like wget and curl.
RUN DEBIAN_FRONTEND=noninteractive apt-get install \
    wget curl unzip -y < /dev/null
# python3-setuptools

# Install the AWS CLI.
RUN curl "https://s3.amazonaws.com/aws-cli/awscli-bundle.zip" -o "awscli-bundle.zip"
RUN unzip awscli-bundle.zip
RUN python3 ./awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws
RUN rm -rf awscli-bundle.zip awscli-bundle awscli-bundle.zip

COPY docker/entrypoint.sh ./docker/entrypoint.sh
RUN chmod 744 ./docker/entrypoint.sh

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Setup the Open Data Cube configuration.
ARG ODC_DB_HOSTNAME="odc-db"
ARG ODC_DB_DATABASE="datacube"
ARG ODC_DB_USER="dc_user"
ARG ODC_DB_PASSWORD="localuser1234"
ARG ODC_DB_PORT="5432"
ENV ODC_DB_HOSTNAME=${ODC_DB_HOSTNAME} \
    ODC_DB_DATABASE=${ODC_DB_DATABASE} \
    ODC_DB_USER=${ODC_DB_USER} \
    ODC_DB_PASSWORD=${ODC_DB_PASSWORD} \
    ODC_DB_PORT=${ODC_DB_PORT}

ARG WORKDIR=/manual_indexer
WORKDIR $WORKDIR

ENTRYPOINT ["/build/docker/entrypoint.sh"]
CMD ["tail -f /dev/null"]
