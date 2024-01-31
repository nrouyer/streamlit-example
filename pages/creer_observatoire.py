import streamlit as st
import neo4j
import requests
from bs4 import BeautifulSoup
from neo4j import GraphDatabase
from googlesearch import search

st.set_page_config(
        page_title="Créer Observatoire",
)

from st_pages import show_pages_from_config

show_pages_from_config()

st.title("📝 Créer un nouvel observatoire sur les accidents")

question = st.text_input(
    "Renseigner les termes de recherche",
    placeholder="accident+voiture",
)

#term = "accident+moto+grievement"
if question:
    st.write('Recherche avec les termes : ', question)
    
    results = search(question, lang="fr", num_results=50, advanced=True)
        
    # Neo4j connection details
    url = st.secrets["AAA_URI"]
    username = st.secrets["AAA_USERNAME"]
    password = st.secrets["AAA_PASSWORD"]
    
    # Create a driver instance
    driver = GraphDatabase.driver(url, auth=(username, password))

    # Function to add an event to the Neo4j database
    def add_article(session, url, description):
        session.run("MERGE (a:Article {url: $url}) ON CREATE SET a.description = $description, a.dateCreation=datetime()", url=url, description=description)

    def update_article(session, url, text):
        session.run("MATCH (a:Article {url: $url}) ON MATCH SET a.text = $text", url=url, text=text)

    with st.spinner('Collecte des articles...'):
            # Insert data from the DataFrame
            with driver.session() as session:
                for result in results:
                    add_article(session, result.url, result.description)

                for result in results:
                    page = requests.get(result.url)
                    soup = BeautifulSoup(page.content, "html.parser")
                    paragraphs = soup.find_all("p", class_="")
                    if paragraphs:
                            text = ""
                            for paragraph in paragraphs:
                                    text = text + paragraph.text.strip()
                            if text:
                                    st.info('le texte n est pas vide', icon="ℹ️")
                                    update_article(session, result.url, text)

    st.success('Collecte des articles terminée !')        
    
    # Close the driver
    driver.close()
