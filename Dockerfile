# Dockerfile -- lives at the repo root. the recipe the host uses to build DocTalk's box.

# start from a slim official Python matching our 3.11 (slim = smaller, faster builds).
FROM python:3.11-slim

# the host runs the container as user id 1000, NOT root. make that same user FIRST,
# else files end up owned by root and the app can't write logs/ or the chroma store.
RUN useradd -m -u 1000 user
USER user

# give the app a home it owns, and put pip's user-installed binaries
# (uvicorn, streamlit) on the PATH so start.sh can actually find them.
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# everything below happens inside this folder, which "user" owns.
WORKDIR /home/user/app

# copy the whole project in, handing ownership to "user" (that's --chown).
# .dockerignore keeps the junk (.venv, .git, artifacts, .env) OUT of this copy.
COPY --chown=user . .

# install every pinned dep. the last line of requirements.txt is "-e ." so this
# also installs our own doctalk package from src/. --no-cache-dir keeps it lean.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# note that the app listens on 8080 (the public port start.sh binds Streamlit to).
# EXPOSE is just documentation -- the host maps the real traffic to this port.
EXPOSE 8080

# boot by running our two-server script.
CMD ["bash", "start.sh"]