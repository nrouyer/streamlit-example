import streamlit as st


st.title("📝 Creer un graphe de connaissances sur les accidents")

question = st.text_input(
    "Renseigner les termes de recherche",
    placeholder="accident+voiture",
)

