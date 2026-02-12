import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    st.set_page_config(page_title="CloudWalk Chat")
    st.title("CloudWalk Chat")

    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
    user_id = os.environ.get("DEFAULT_USER_ID", "user123")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Digite sua mensagem")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        payload = {"message": prompt, "user_id": user_id}
        response = requests.post(f"{backend_url.rstrip('/')}/message", json=payload, timeout=300)
        data = response.json()
        answer = data.get("response", "")

        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)


if __name__ == "__main__":
    main()