FROM opendatacube/datacube-core:1.7

ENV CURL_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"

WORKDIR /Datacube

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Install CA certificates (partly for S3 access).
RUN apt-get update && apt-get install ca-certificates -y && \
    rm -rf /var/lib/apt/lists/*
RUN echo "\nexport CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt" >> ~/.profile
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

COPY docker/entrypoint.sh ./entrypoint.sh
RUN chmod 744 entrypoint.sh

WORKDIR /Datacube/manual_indexer

ENTRYPOINT ["/Datacube/entrypoint.sh"]
CMD ["tail -f /dev/null"]
