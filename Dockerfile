FROM ubuntu
WORKDIR /code
COPY requirements.txt requirements.txt
RUN  apt-get update && DEBIAN_FRONTEND="noninteractive" apt-get install --no-install-recommends \
        git \
        python3-pip -y && pip3 install -r requirements.txt --no-cache-dir && apt-get autoremove -y && apt-get autoclean -y && rm -rf /var/lib/apt/lists/*
COPY CahBot.py .
COPY modules modules
COPY packs.pickle .
USER 1001
ENTRYPOINT ["python3","CahBot.py"]