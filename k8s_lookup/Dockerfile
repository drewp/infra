FROM ubuntu:jammy-20220428
RUN echo 2022-06-20 && apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y udns-utils oping curl
CMD ["sleep", "1d"]
