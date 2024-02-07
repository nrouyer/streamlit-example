import streamlit as st
import neo4j
import requests
from bs4 import BeautifulSoup
from neo4j import GraphDatabase
from googlesearch import search
import openai
from retry import retry
import re
from string import Template
import json
import ast
import time
import pandas as pd
import glob
from timeit import default_timer as timer

st.set_page_config(
        page_title="Nouvel Observatoire",
)

from st_pages import show_pages_from_config

show_pages_from_config()

st.title("🆕 Nouvel observatoire sur les accidents")

constraints_cyp="""
CREATE CONSTRAINT node_key_personne_id IF NOT EXISTS FOR (n:Personne) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_groupe_id IF NOT EXISTS FOR (n:Groupe) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_impact_id IF NOT EXISTS FOR (n:Impact) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_evenement_id IF NOT EXISTS FOR (n:Evenement) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_typeevenement_id IF NOT EXISTS FOR (n:TypeEvenement) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_article_id IF NOT EXISTS FOR (n:Article) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_document_id IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_facteur_id IF NOT EXISTS FOR (n:Facteur) REQUIRE n.id IS NODE KEY;
CREATE CONSTRAINT node_key_solution_id IF NOT EXISTS FOR (n:Solution) REQUIRE n.id IS NODE KEY;
"""

constraint_personne_id = """
CREATE CONSTRAINT node_key_personne_id IF NOT EXISTS FOR (n:Personne) REQUIRE n.id IS NODE KEY;
"""
constraint_groupe_id = """
CREATE CONSTRAINT node_key_groupe_id IF NOT EXISTS FOR (n:Groupe) REQUIRE n.id IS NODE KEY;
"""
constraint_impact_id = """
CREATE CONSTRAINT node_key_impact_id IF NOT EXISTS FOR (n:Impact) REQUIRE n.id IS NODE KEY;
"""
constraint_evenement_id = """
CREATE CONSTRAINT node_key_evenement_id IF NOT EXISTS FOR (n:Evenement) REQUIRE n.id IS NODE KEY;
"""
constraint_typeevenement_id = """
CREATE CONSTRAINT node_key_typeevenement_id IF NOT EXISTS FOR (n:TypeEvenement) REQUIRE n.id IS NODE KEY;
"""
constraint_article_id = """
CREATE CONSTRAINT node_key_article_id IF NOT EXISTS FOR (n:Article) REQUIRE n.id IS NODE KEY;
"""
constraint_document_id = """
CREATE CONSTRAINT node_key_document_id IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS NODE KEY;
"""
constraint_facteur_id = """
CREATE CONSTRAINT node_key_facteur_id IF NOT EXISTS FOR (n:Facteur) REQUIRE n.id IS NODE KEY;
"""
constraint_solution_id = """
CREATE CONSTRAINT node_key_solution_id IF NOT EXISTS FOR (n:Solution) REQUIRE n.id IS NODE KEY;
"""


prompt1="""Depuis la description de l'accident ci-dessous, extraire les entités et les relations décrites dans le format mentionné :
0. TOUJOURS TERMINER LA RÉPONSE. Ne jamais envoyer de réponses partielles.
1. Tout d'abord, recherchez ces types d'entités dans le texte et générez-les dans un format séparé par des virgules, similaire à celui des types d'entités. La propriété `id` de chaque entité doit être alphanumérique et unique parmi les entités. Vous ferez référence à cette propriété pour définir la relation entre les entités. Ne créez pas de nouveaux types d'entités qui ne sont pas mentionnés ci-dessous. Le document doit être résumé et stocké dans l'entité Article sous la propriété `description`. Vous devrez générer autant d'entités que nécessaire selon les types ci-dessous :
    Types d'entités :
    label:'Evenement',id:string,description:string,date:datetime,duree:string,lieu:string //Evenement c'est un événement qui s'est produit, par exemple un accident
    label:'TypeEvenement',id:string,type:string //TypeEvenement c'est le type d'événement qui s'est produit
    label:'Article',id:string,urlMedia:string,uri:string,url:string,journaliste:string,synthese:string,date:datetime,titre:string,media:string,description:string //Entité Article ; la propriété `id` c'est le nom de l'article, en lowercase & camel-case & qui commence toujours par un caractère alphabétique
    label:'Document',id:string,description:string //Entité Document ; la propriété `id` c'est le nom de du document, en lowercase & camel-case & qui commence toujours par un caractère alphabétique
    label:'Facteur',id:string,name:string // Entité Facteur c'est le facteur explicatif de l'événement; la propriété `id` c'est le nom du facteur, en lowercase & camel-case & qui commence toujours par un caractère alphabétique
    label:'Solution',id:string,name:string,description:string,when:string // Entité Solution c'est la solution qui pourrait aider à résoudre l'événement qui s'est produit ; la propriété `id` c'est le nom du facteur, en lowercase & camel-case & qui commence toujours par un caractère alphabétique
    label:'Impact',id:string,name:string,description:string // Entité Impact c'est l'impact de l'événement qui s'est produit ; la propriété `id` c'est le nom de l'impact, en lowercase & camel-case & qui commence toujours par un caractère alphabétique
    label:'Personne',id:string,prenom:string,nom:string,age:string,sexe:string,nationalite:string,profession:string,passeJudiciare:string // Entité Personne c'est une personne liée à l'événement qui s'est produit ; la propriété `id` c'est le nom de la personne, en lowercase & camel-case & qui commence toujours par un caractère alphabétique
    label:'Groupe',id:string,nom:string,nature:string,nombreMembres:integer // Entité Groupe c'est un groupe auquel une personne est liée ; la propriété `id` c'est le nom du groupe, en lowercase & camel-case & qui commence toujours par un caractère alphabétique
2. Ensuite, générez chaque relation comme un triplet de source, relation et cible. Pour faire référence à l'entité source et à l'entité cible, utilisez leur propriété `id` respective. Vous devrez générer autant de relations que nécessaire, comme défini ci-dessous :
    Types de relations :
    Personne|A_BLESSE|Personne
    Personne|A_TUE|Personne
    Personne|CONNAIT|Personne
    Personne|EN_LIEN_AVEC|Personne
    Personne|FAIT_PARTIE_DE|Groupe
    Personne|VEUT_FAIRE_PARTIE_DE|Groupe
    Personne|INFLUENCE|Groupe
    Personne|DIRIGE|Groupe
    Personne|VICTIME_DE|Evenement
    Personne|AUTEUR_DE|Evenement
    Personne|INTERVIENT_DANS|Evenement
    Personne|DOCUMENTE|Evenement
    Personne|TEMOIN_DE|Evenement
    Personne|COVICTIME_DE|Evenement
    Evenement|A|Impact
    Impact|SUR|Personne
    Evenement|SUIT|Evenement
    Evenement|A|TypeEvenement
    Article|DOCUMENTE|Evenement
    Document|PROUVE|Evenement
    Facteur|EXPLIQUE|Evenement
    Evenement|A|Solution

Le resultat devrait ressembler à :
{
    "entites": [{"label":"Evenement","id":string,"description":string,"date":datetime,"duree":string,"lieu":string}],
    "relations": [{"personne1|A_TUE|personne2"}]
}

Accident :
$ctext
"""

openai.api_key = st.secrets["OPENAI_KEY"]

# GPT-4 or GPT-3.5 Prompt to complete
@retry(tries=2, delay=5)
def process_gpt(system,
                prompt):

    #completion = openai.ChatCompletion.create(
        # engine="gpt-3.5-turbo",
        #model="gpt-3.5-turbo",
        #max_tokens=2400,
        #model="gpt-4",
        #max_tokens=4096,
        # Try to be as deterministic as possible
        #temperature=0,
        #messages=[
            #{"role": "system", "content": system},
            #{"role": "user", "content": prompt},
        #]
    #)
    completion = openai.chat.completions.create(
      model="gpt-4",
      temperature=0,
      messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
      ],
    ) 

    nlp_results = completion.choices[0].message.content
    return nlp_results

def clean_text(text):
  clean = "\n".join([row for row in text.split("\n")])
  clean = re.sub(r'\(fig[^)]*\)', '', clean, flags=re.IGNORECASE)
  return clean

def run_completion(prompt, results, ctext):
    try:
      system = "Vous êtes un expert Accident aidant qui extrait des informations pertinentes et les stocke dans un graphe de connaissances Neo4j"
      pr = Template(prompt).substitute(ctext=ctext)
      res = process_gpt(system, pr)
      results.append(json.loads(res.replace("\'", "'")))
      return results
    except Exception as e:
        print(e)

#pre-processing results for uploading into Neo4j - helper function:
def get_prop_str(prop_dict, _id):
    s = []
    for key, val in prop_dict.items():
      if key != 'label' and key != 'id':
         s.append(_id+"."+key+' = "'+str(val).replace('\"', '"').replace('"', '\"')+'"')
    return ' ON CREATE SET ' + ','.join(s)

def get_cypher_compliant_var(_id):
    return "_"+ re.sub(r'[\W_]', '', _id)

def generate_cypher(in_json):
    e_map = {}
    e_stmt = []
    r_stmt = []
    e_stmt_tpl = Template("($id:$label{id:'$key'})")
    r_stmt_tpl = Template("""
      MATCH $src
      MATCH $tgt
      MERGE ($src_id)-[:$rel]->($tgt_id)
    """)
    for obj in in_json:
      for j in obj['entites']:
          props = ''
          label = j['label']
          id = j['id']
          if label == 'Groupe':
            id = 'g'+str(time.time_ns())
          elif label == 'Personne':
            id = 'p'+str(time.time_ns())
          elif label == 'Evenement':
            id = 'e'+str(time.time_ns())
          elif label == 'TypeEvenement':
            id = 'te'+str(time.time_ns())
          elif label == 'Article':
            id = 'a'+str(time.time_ns())
          elif label == 'Document':
            id = 'd'+str(time.time_ns())
          elif label == 'Facteur':
            id = 'f'+str(time.time_ns())
          elif label == 'Solution':
            id = 's'+str(time.time_ns())
          elif label == 'Impact':
            id = 'i'+str(time.time_ns())
          else:
            id = 'z'+str(time.time_ns())
          # print(j['id'])
          varname = get_cypher_compliant_var(j['id'])
          stmt = e_stmt_tpl.substitute(id=varname, label=label, key=id)
          e_map[varname] = stmt
          e_stmt.append('MERGE '+ stmt + get_prop_str(j, varname))
          print(e_stmt)

      for st in obj['relations']:
          print(st)
          rels = st.split("|")
          #rels = st.split(",")
          #print(rels)
          #src_id = get_cypher_compliant_var(st['source'])
          #rel = st['relation']
          #tgt_id = get_cypher_compliant_var(st['cible'])
          src_id = get_cypher_compliant_var(rels[0].strip())
          rel = rels[1]
          tgt_id = get_cypher_compliant_var(rels[2].strip())
          #print(src_id)
          #print(rel)
          #print(tgt_id)
          stmt = r_stmt_tpl.substitute(
              src_id=src_id, tgt_id=tgt_id, src=e_map[src_id], tgt=e_map[tgt_id], rel=rel)
          print(stmt)
          r_stmt.append(stmt)

    return e_stmt, r_stmt

def graph_article(session, text):
  prompts = [prompt1]
  resultats = []
  for p in prompts:
    resultats = run_completion(p, resultats, clean_text(text))
    if resultats:
      ent_cyp, rel_cyp = generate_cypher(resultats)
      # ingérer les entités
      st.info('Ingestion des entités', icon="ℹ️") 
      session.run(ent_cyp)
      # ingérer les relations
      st.info('Ingestion des relations', icon="ℹ️") 
      session.run(rel_cyp)
    

question = st.text_input(
    "Renseigner les termes de recherche",
    placeholder="accident+voiture",
)

#term = "accident+moto+grievement"
if question:
    st.write('Recherche avec les termes : ', question)
    
    results = search(question, lang="fr", num_results=5, advanced=True)
        
    # Neo4j connection details
    url = st.secrets["AAA_URI"]
    username = st.secrets["AAA_USERNAME"]
    password = st.secrets["AAA_PASSWORD"]
    
    # Create a driver instance
    driver = GraphDatabase.driver(url, auth=(username, password))        

    with st.spinner('Collecte des articles...'):
        # Insert data from the DataFrame
        
        with driver.session() as session:
            #st.info('Mise à jour des contraintes', icon="ℹ️")    
            #session.run(constraint_personne_id)
            #session.run(constraint_groupe_id)
            #session.run(constraint_impact_id)
            #session.run(constraint_evenement_id)
            #session.run(constraint_typeevenement_id)
            #session.run(constraint_article_id)
            #session.run(constraint_document_id)
            #session.run(constraint_facteur_id)
            #session.run(constraint_solution_id)    

            st.info('Enrichissement des articles', icon="ℹ️")    
            for result in results:
                page = requests.get(result.url)
                soup = BeautifulSoup(page.content, "html.parser")
                paragraphs = soup.find_all("p", class_="")
                if paragraphs:
                    text = ""
                    for paragraph in paragraphs:
                        text = text + paragraph.text.strip()
                    if text:
                        #st.info('texte : ' + text, icon="ℹ️")
                        # update_article(session, result.url, text)
                        graph_article(session, text)   
            st.info('Fin enrichissement des articles', icon="ℹ️")    
    st.success('Collecte des articles terminée !')        
    
    # Close the driver
    driver.close()
