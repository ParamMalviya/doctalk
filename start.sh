#!/usr/bin/env bash
# start.sh -- lives at the repo root. the container runs THIS on boot.
# the host gives us one container but DocTalk is two servers, so we launch both.

# 1) FastAPI backend on port 8000 -- stays INTERNAL, the browser never hits it.
#    Streamlit calls it on 127.0.0.1:8000 (that's why API_URL doesn't change).
#    the "&" shoves it into the background so the script keeps going.
uvicorn main:app --host 0.0.0.0 --port 8000 &

# 2) Streamlit UI on the public port (${PORT:-8080}) -- the one port the host
#    exposes to the world. runs in the FOREGROUND so it stays the container's
#    main process. the flags below keep it working behind a hosting proxy:
#      --server.headless true               -> don't try to pop open a browser
#      --server.enableCORS false            } let the app work behind the host's
#      --server.enableXsrfProtection false  } proxy; without the xsrf one the pdf
#                                             uploader silently dies
#      --server.fileWatcherType none        -> no dev hot-reload in prod
streamlit run ui/streamlit_app.py \
    --server.port ${PORT:-8080} \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --server.fileWatcherType none