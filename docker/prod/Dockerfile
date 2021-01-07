FROM opendatacube/datacube-core:1.7
# jcrattzama/datacube-core:1.7

ENV CURL_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"

ARG WORKDIR=/manual_indexer
WORKDIR /build

# Install CA certificates (partly for S3 access).
RUN apt-get update && apt-get install ca-certificates -y && \
    rm -rf /var/lib/apt/lists/*
RUN echo "\nexport CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt" >> ~/.profile
# Source the ~/.profile file.
RUN . ~/.profile

# Install some system utilities like wget and curl.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install \
        wget curl unzip -y < /dev/null && \
    rm -rf /var/lib/apt/lists/*

# Install the AWS CLI.
RUN curl "https://s3.amazonaws.com/aws-cli/awscli-bundle.zip" -o "awscli-bundle.zip"
RUN unzip awscli-bundle.zip
RUN python3 ./awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws
RUN rm -rf awscli-bundle.zip awscli-bundle awscli-bundle.zip

COPY docker/entrypoint.sh ./docker/entrypoint.sh
RUN chmod 744 ./docker/entrypoint.sh

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

WORKDIR $WORKDIR

COPY datasets/ .
COPY utils/ utils/

ENTRYPOINT ["/build/docker/entrypoint.sh"]
CMD ["tail -f /dev/null"]
