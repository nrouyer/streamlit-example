import streamlit as st


st.title("📝 Créer un nouvel observatoire sur les accidents")

question = st.text_input(
    "Renseigner les termes de recherche",
    placeholder="accident+voiture",
)

