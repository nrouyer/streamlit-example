import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import neo4j as neo4j
import googlesearch as googlesearch
import langchain
import langchain_community

"""
# Observatoire des accidents
"""

st.image('images/chatgpt_accident.png', caption='Accidents')

openai_api_key = st.secrets["OPENAI_KEY"]

from langchain_community.llms import OpenAI
from langchain_community.graphs import Neo4jGraph
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.embeddings.openai import OpenAIEmbeddings

url = st.secrets["AAA_URI"]
username = st.secrets["AAA_USERNAME"]
password = st.secrets["AAA_PASSWORD"]
graph = Neo4jGraph(
    url=url,
    username=username,
    password=password
)


llm = OpenAI()

vectorstore = Neo4jVector.from_existing_graph(
    OpenAIEmbeddings(),
    url=url,
    username=username,
    password=password,
    index_name='eventdescription',
    node_label="Event",
    text_node_properties=['description'],
    embedding_node_property='embedding',
)

vector_qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(), chain_type="stuff", retriever=vectorstore.as_retriever())

# Streamlit layout with tabs
container = st.container()
question = container.text_input("**:blue[Question:]**", "")

if question:
    tab1, tab2 = st.tabs(["No-RAG", "Basic RAG"])
    with tab1:
        st.markdown("**:blue[No-RAG.] LLM only. Purely generated answer:**")
        st.write(llm(question))
    with tab2:
        st.markdown("**:blue[Basic RAG.] Answer from vector search only:**")
        st.write(vector_qa.run(question))
    
