FROM python:3.7-slim-buster

USER 0
RUN groupadd -g 1000 -r debian && \
  useradd -u 1000 -r -g debian -m -d /home/debian debian

WORKDIR /usr/src/app
COPY switch_mgmt.py .
COPY requirements.txt .

# By best practices, don't run the code with root user
RUN chgrp -R 1000 /usr/src/app && chmod -R g=u /usr/src/app
USER 1000

# Install extra requirements for actions code, if necessary (uncomment next line)
RUN python3 -m pip install -t .local --upgrade pip && \
    python3 -m pip install -t .local --upgrade --no-cache-dir -r requirements.txt
ENV PATH "/usr/src/app/.local/bin:/bin:/usr/local/bin:/usr/bin:/bin"
ENV PYTHONPATH "/usr/src/app/.local/:/opt/venv/:/usr/local/"

CMD [ "python3", "./switch_mgmt.py" ]
