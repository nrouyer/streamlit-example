# GPT-4 or GPT-3.5 Prompt to complete
@retry(tries=2, delay=5)
def process_gpt(system,
                prompt):

    completion = openai.ChatCompletion.create(
        # engine="gpt-3.5-turbo",
        model="gpt-3.5-turbo",
        max_tokens=2400,
        # Try to be as deterministic as possible
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
    )
    nlp_results = completion.choices[0].message.content
    return nlp_results

def run_completion(prompt, results, ctext):
    try:
      system = "Vous êtes un expert Accident aidant qui extrait des informations pertinentes et les stocke dans un graphe de connaissances Neo4j"
      pr = Template(prompt).substitute(ctext=ctext)
      res = process_gpt(system, pr)
      results.append(json.loads(res.replace("\'", "'")))
      return results
    except Exception as e:
        print(e)

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
