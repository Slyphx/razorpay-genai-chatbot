import boto3
import streamlit as st
import os
import traceback
import logging
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

try:
    kb_client = boto3.client("bedrock-agent-runtime")
    logger.info("AWS Bedrock client initialized successfully.")
except Exception as e:
    logger.error("Failed to initialize AWS clients: %s", e)
    raise

KB_ID = st.secrets["BEDROCK_KB_ID"]
MODEL_ARN = st.secrets["MODEL_ARN"]


if not KB_ID or not MODEL_ARN:
    logger.warning("BEDROCK_KB_ID or MODEL_ARN not set in environment variables!")

def get_kb_response(question: str) -> str:
    logger.debug(f"get_kb_response() called with KB_ID={KB_ID}, modelArn={MODEL_ARN}, question='{question}'")

    if not KB_ID or not MODEL_ARN:
        return "Error: Missing KB_ID or MODEL_ARN. Please check your .env file."

    try:
        response = kb_client.retrieve_and_generate(
            input={"text": question},
            retrieveAndGenerateConfiguration={
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KB_ID,
                    "modelArn": MODEL_ARN
                },
                "type": "KNOWLEDGE_BASE"
            }
        )
        logger.debug("KB response raw: %s", response)
        return response["output"]["text"]

    except Exception as e:
        logger.error("Error during retrieve_and_generate: %s", e)
        traceback.print_exc()
        return f"Error querying KB: {e}"


def main():
    st.set_page_config(page_title="Razorpay KB Chatbot", page_icon="💬", layout="centered")
    st.header("💬 Chat with Razorpay Knowledge Base")

    st.sidebar.header("🔎 Debug Info")
    st.sidebar.write(f"KB_ID: {KB_ID or '❌ Not Set'}")
    st.sidebar.write(f"MODEL_ARN: {MODEL_ARN or '❌ Not Set'}")
    st.sidebar.markdown("---")
    st.sidebar.markdown(
    '<a href="http://howitworksrazorpay.s3-website-us-east-1.amazonaws.com/" target="_blank">📄 How it works</a>',
    unsafe_allow_html=True)

    preset_questions = [
        "List all the OWASP Top 10 for LLMs?",
        "Who won the F1 Italian Grand Prix?",
        "What is a Knowledge Base in AWS Bedrock?",
        "Summarize threat vectors in an LLM-based RAG pipeline."
    ]

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.show_presets = True 

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.show_presets and not st.session_state.messages:
        st.markdown("### ✨ Try asking:")
        cols = st.columns(2)
        for i, q in enumerate(preset_questions):
            if cols[i % 2].button(q):
                # simulate asking the preset question
                st.session_state.show_presets = False
                st.session_state.messages.append({"role": "user", "content": q})
                with st.chat_message("user"):
                    st.markdown(q)

                with st.chat_message("assistant"):
                    with st.spinner("Querying KB..."):
                        answer = get_kb_response(q)
                        st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()

    # Chat input box
    if question := st.chat_input("Type your question here..."):
        st.session_state.show_presets = False  # hide presets after first query
        logger.info("User asked: %s", question)

        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Querying KB..."):
                answer = get_kb_response(question)
                st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    logger.info("Starting Streamlit app...")
    main()
