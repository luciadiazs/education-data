import os
import json
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import re  # Important for regex in find_relevant_chunks

# Streamlit Configuration
st.set_page_config(page_title="Interactive Education Database", layout="centered")

with st.sidebar:
    st.title('Interactive Education Database')
    st.markdown('''
    ## About this bot
    This is a chatbot that allows you to talk to the PDFs used for the Education, English Learning, and Youth in Peru.
    ''')

load_dotenv()

# Make sure this definition is before its call
def load_chunks_from_json(input_file='docs_chunks_spotlight.json'):
    with open(input_file, 'r', encoding='utf-8') as f:
        docs_chunks = json.load(f)
    return docs_chunks

docs_chunks = load_chunks_from_json()  # Load the chunks at the beginning

# Define the system prompt globally if it does not change
system_prompt = "You are an expert in the documents provided, which are documents pertaining to the state of Peruvian education and youth. Answer the questions based on the data in the documents."

# Instantiate the OpenAI client outside the main function so it's available globally
client = OpenAI(api_key=st.secrets["openai_key"])

def find_relevant_chunks(question, docs_chunks, max_chunks=5):
    # Tokenize the question to extract significant keywords
    question_keywords = set(re.findall(r'\w+', question.lower()))
    relevance_scores = []

    # Calculate a relevance score for each chunk (it can be the count of matching keywords)
    for chunk in docs_chunks:
        chunk_text = chunk["content"].lower()
        chunk_keywords = set(re.findall(r'\w+', chunk_text))
        common_keywords = question_keywords.intersection(chunk_keywords)
        relevance_scores.append((len(common_keywords), chunk))

    # Sort the chunks by their relevance score, from highest to lowest
    relevant_chunks = [chunk for _, chunk in sorted(relevance_scores, key=lambda x: x[0], reverse=True)]

    # Return the top N most relevant chunks
    return relevant_chunks[:max_chunks]

def send_question_to_openai(question, docs_chunks):
    # Find the most relevant chunks for the question
    relevant_chunks = find_relevant_chunks(question, docs_chunks)
    
    # Build the full prompt with the system prompt and the relevant chunks of text
    prompt_text = system_prompt + "\n\n" + "\n\n".join([chunk["content"] for chunk in relevant_chunks]) + "\n\nQuestion: " + question

    # Call the OpenAI API with the complete prompt using the client
    response = client.completions.create(
        model="gpt-3.5-turbo",
        prompt=prompt_text,
        temperature=0.7,  # Adjust as necessary
        max_tokens=150,   # Adjust as necessary
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    
    # Return the text of the first choice (strip any leading/trailing whitespace)
    return response.choices[0].text.strip()

# Main interaction logic needs to be in the global scope for Streamlit to execute it correctly
if "messages" not in st.session_state:
    st.session_state["messages"] = []

st.header("Interactive Education Database 💬")
prompt = st.text_input("Your inquiry:", "")

if st.button("Send") and prompt:
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)

    with st.spinner("Generating answer..."):
        response_text = send_question_to_openai(prompt, docs_chunks)
        assistant_message = {"role": "assistant", "content": response_text}
        st.session_state.messages.append(assistant_message)

for index, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.text_area("Question", value=message["content"], height=75, disabled=True, key=f"user_{index}")
    else:  # message["role"] == "assistant"
        st.text_area("Answer", value=message["content"], height=100, disabled=True, key=f"assistant_{index}")
