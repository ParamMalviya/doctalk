# Dockerfile -- lives at the repo root. the recipe HF uses to build DocTalk's box.

# start from a slim official Python matching our 3.11 (slim = smaller, faster builds).
FROM python:3.11-slim

# HF runs the container as user id 1000, NOT root. make that same user FIRST,
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

# note that the app speaks on 7860 (HF's one public door). EXPOSE is just a label
# -- HF reads the REAL port from app_port in the Space's README later.
EXPOSE 7860

# boot by running our two-server script. "bash start.sh" (not "./start.sh")
# dodges the executable-bit + Windows line-ending headaches.
CMD ["bash", "start.sh"]