# Importing required packages
import streamlit as st
import openai
import uuid
import time
import io
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

# Initialize OpenAI client
client = OpenAI()
MODEL = "gpt-4-1106-preview"

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "run" not in st.session_state:
    st.session_state.run = {"status": None}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "retry_error" not in st.session_state:
    st.session_state.retry_error = 0

# Set up the page
st.set_page_config(page_title="GPT Assistant")
st.sidebar.title("Custom GPT")
st.sidebar.divider()
st.sidebar.markdown("Assistant GPT: Name")
st.sidebar.divider()

# Initialize OpenAI assistant
if "assistant" not in st.session_state:
    openai.api_key = os.getenv('OPENAI_API_KEY')
    st.session_state.assistant = openai.beta.assistants.retrieve(os.getenv('OPENAI_ASSISTANT'))
    st.session_state.thread = client.beta.threads.create(
         metadata={'session_id': st.session_state.session_id}
     )

# Display chat messages
elif hasattr(st.session_state.run, 'status') and st.session_state.run.status == "completed":
    st.session_state.messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread.id
    )
    for message in reversed(st.session_state.messages.data):
        if message.role in ["user", "assistant"]:
            with st.chat_message(message.role):
                for content_part in message.content:
                    message_text = content_part.text.value
                    st.markdown(message_text)

# Chat input and message creation
if prompt := st.chat_input("Wie kann ich Ihnen helfen?"):
    with st.chat_message('user'):
        st.write(prompt)

    message_data = {
        "thread_id": st.session_state.thread.id,
        "role": "user",
        "content": prompt
    }

    st.session_state.messages = client.beta.threads.messages.create(**message_data)

    st.session_state.run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread.id,
        assistant_id=st.session_state.assistant.id,
    )
    if st.session_state.retry_error < 3:
        time.sleep(1)
        st.rerun()

# Handle run status
if hasattr(st.session_state.run, 'status'):
    if st.session_state.run.status == "running":
        with st.chat_message('assistant'):
            st.write("Antwort wird erzeugt ......")
        if st.session_state.retry_error < 3:
            time.sleep(1)
            st.rerun()

    elif st.session_state.run.status == "failed":
        st.session_state.retry_error += 1
        with st.chat_message('assistant'):
            if st.session_state.retry_error < 3:
                st.write("Ausführung fehlgeschlagen, erneuter Versuch ......")
                time.sleep(3)
                st.rerun()
            else:
                st.error("FEHLER: Die OpenAI-API verarbeitet derzeit zu viele Anfragen. Bitte versuchen Sie es später erneut ......")

    elif st.session_state.run.status != "completed":
        st.session_state.run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread.id,
            run_id=st.session_state.run.id,
        )
        if st.session_state.retry_error < 3:
            time.sleep(3)
            st.rerun()
