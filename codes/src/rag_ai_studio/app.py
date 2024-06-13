import streamlit as st
import yaml
from dotenv import load_dotenv
from rag_ai_studio.chat import chat_completion

load_dotenv("configs/environment_variables.env")


# set streamlit-chat very first intial message in chat history
def get_initial_message():
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI Tutor. Who anwers brief questions about CA documents.",
        }
    ]
    return messages


st.set_page_config(
    page_title="Ask me Anything", layout="wide", page_icon="images/favicon.png"
)

if "model_config" not in st.session_state:
    with open("configs/user_config.yaml") as f:
        model_config = yaml.safe_load(f)
    st.session_state["model_config"] = model_config

# Initialize all session state variables
if "submit_disabled" not in st.session_state:
    st.session_state.submit_disabled = False

if "disable_text_area" not in st.session_state:
    st.session_state.disable_text_area = False

if "track_radio_feedback" not in st.session_state:
    st.session_state["track_radio_feedback"] = False

if "generated" not in st.session_state:
    st.session_state["generated"] = []

if "past" not in st.session_state:
    st.session_state["past"] = []

if "messages" not in st.session_state:
    st.session_state["messages"] = get_initial_message()

if "latency_time" not in st.session_state:
    st.session_state["latency_time"] = [0, 0]

if "query_timestamp" not in st.session_state:
    st.session_state["query_timestamp"] = ""

if "submit_feedback_state" not in st.session_state:
    st.session_state["submit_feedback_state"] = False

if "document_table" not in st.session_state:
    st.session_state["document_table"] = ""


def disable_submit():
    # call when we click on user query submit button
    st.session_state.submit_disabled = False
    st.session_state.disable_text_area = False


def track_radio_feedback():
    # call when we are recording the feedback from radio button
    st.session_state["track_radio_feedback"] = False
    st.session_state["submit_feedback_state"] = True
    st.session_state.submit_disabled = False
    st.session_state.disable_text_area = False


st.divider()


background_color = "#B8EFF9"  # Use your desired color code

# Add the background color and text inside a div using HTML and CSS
custom_html = f"""
<div style="background-color:{background_color}; padding:10px; border-radius:10px; text-align:center;">
    <h1 style="color:Black;"> <span style="font-size: 24px;">Welcome to Azure OpenAI Intelligent Chatbot!</span>
</div>
"""

# Render the HTML using st.markdown
st.markdown(custom_html, unsafe_allow_html=True)
st.title("Ask me anything!")


st.sidebar.image("images/logo.png", use_column_width="always")
st.sidebar.title("Application Parameters")
st.sidebar.write(
    '<p style="font-size: 20px;">Welcome <span style="font-style: italic;">Admin!</span></p>',
    unsafe_allow_html=True,
)


def update_chat(messages, role, content):
    messages.append({"role": role, "content": content})
    return messages


def main_func():
    # Sidebar options
    with st.sidebar:
        temperature = st.slider(
            "Select Temperature",
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            value=st.session_state["model_config"]["model"]["temperature"],
        )
        max_token = st.slider(
            "Select max Token",
            min_value=0,
            max_value=5000,
            step=500,
            value=st.session_state["model_config"]["model"]["max_tokens"],
        )
        summarize_prompt = st.text_area(
            label="Summarize Prompt",
            value=st.session_state["model_config"]["prompt"]["user_prompt"],
            placeholder="Please provide a summarize prompt:",
        )
        if temperature:
            st.session_state["model_config"]["model"]["temperature"] = temperature
        if max_token:
            st.session_state["model_config"]["model"]["max_tokens"] = max_token
        if summarize_prompt:
            if not (
                "{question}" in summarize_prompt and "{context}" in summarize_prompt
            ):
                postfix = "\n\nQuestion:'{question}' \n\nContext: '{context}'"
            else:
                postfix = ""
            st.session_state["model_config"]["prompt"]["user_prompt"] = (
                summarize_prompt + postfix
            )

    # Displaying old messages
    with st.spinner("generating..."):
        messages = st.session_state["messages"]
        # messages = update_chat(messages, "user", query)
        for message_ in messages:
            if message_["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(message_["content"])
            if message_["role"] == "assistant":
                result = message_["content"]
                answer = result["choices"][0]["message"]["content"]
                contexts = result["choices"][0]["context"]["contexts"]
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    for idx, context in enumerate(contexts):
                        with st.expander(label=f"Reference {idx+1}"):
                            st.write(context)

    # Interacting with current query
    query = st.chat_input(
        "Enter your queries on openai search engine!",
    )
    if query is not None:
        if query != "":
            # Resetting session state
            st.session_state["track_radio_feedback"] = False
            st.session_state["submit_feedback_state"] = False
            # Get response
            result = chat_completion(
                question=query,
                system_role=st.session_state["model_config"]["prompt"]["system_role"],
                user_prompt=st.session_state["model_config"]["prompt"]["user_prompt"],
                index_name=st.session_state["model_config"]["rag"]["index_name"],
                num_docs=st.session_state["model_config"]["rag"]["num_docs"],
                temperature=st.session_state["model_config"]["model"]["temperature"],
                max_tokens=st.session_state["model_config"]["model"]["max_tokens"],
            )
            # Appending message
            messages = update_chat(messages, "user", query)
            messages = update_chat(messages, "assistant", result)
            st.session_state["messages"] = messages
            answer = result["choices"][0]["message"]["content"]
            contexts = result["choices"][0]["context"]["contexts"]
            with st.chat_message("user"):
                st.markdown(query)
            with st.chat_message("assistant"):
                st.markdown(answer)
                for idx, context in enumerate(contexts):
                    with st.expander(label=f"Reference {idx+1}"):
                        st.write(context)

            with st.form("current_form"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    feedback_message = "Don't forget to log your feedback for each query using the 👍 or 👎"
                    st.markdown(feedback_message, unsafe_allow_html=True)
                with col2:
                    c1, c2 = st.columns(2)
                    with c1:
                        thumbs_up = "Thumbs_up"
                        emo = "👍"
                        st.form_submit_button(
                            emo,
                            # on_click=record_short_feedback,
                            args=(thumbs_up,),
                        )
                    with c2:
                        thumbs_down = "Thumbs_down"
                        emo = "👎"
                        st.form_submit_button(
                            emo,
                            # on_click=record_short_feedback,
                            args=(thumbs_down,),
                        )


main_func()
