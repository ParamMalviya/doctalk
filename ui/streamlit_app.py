import requests
import streamlit as st


# where the FastAPI server is running
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="DocTalk", page_icon="📄")
st.title("📄 DocTalk")
st.caption("Upload a PDF and chat with it. Ask about the document, a GitHub repo, or the web.")


# --- session state: these must survive Streamlit's reruns ---
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "filename" not in st.session_state:
    st.session_state.filename = None
if "messages" not in st.session_state:
    st.session_state.messages = []   # list of {"role": ..., "content": ...}


# --- upload section ---
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file is not None and uploaded_file.name != st.session_state.filename:
    # only upload when it's a NEW file, not on every rerun
    with st.spinner("Ingesting document..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            resp = requests.post(f"{API_URL}/upload", files=files, timeout=120)

            if resp.status_code == 200:
                data = resp.json()
                st.session_state.session_id = data["session_id"]
                st.session_state.filename = uploaded_file.name
                st.session_state.messages = []   # fresh chat for a new doc
                st.success(f"Ready! Ingested {data['num_chunks']} chunks from {data['filename']}.")
            else:
                st.error(f"Upload failed: {resp.text}")
        except Exception as e:
            st.error(f"Could not reach the API: {e}")


# --- chat section (only after a successful upload) ---
if st.session_state.session_id:
    # show the conversation so far
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # the input box at the bottom
    question = st.chat_input("Ask about your document...")

    if question:
        # show the user's message
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # call the API for an answer
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/chat",
                        json={"session_id": st.session_state.session_id, "question": question},
                        timeout=120,
                    )
                    if resp.status_code == 200:
                        answer = resp.json()["answer"]
                    else:
                        answer = f"Error: {resp.text}"
                except Exception as e:
                    answer = f"Could not reach the API: {e}"

                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
else:
    st.info("Upload a PDF above to start chatting.")