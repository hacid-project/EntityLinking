import requests
import json
from SPARQLWrapper import SPARQLWrapper, JSON

# Linking KG
def linkingCMA(term):
    sparql = SPARQLWrapper("https://semantics.istc.cnr.it/hacid/sparql")
    sparql.setCredentials('hacid', 'hacid')
    sparql.setReturnFormat(JSON)
    variable = [term,term]
    sparql.setQuery("""
    PREFIX bif: <http://www.openlinksw.com/schemas/bif#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX naming: <https://w3id.org/hacid/onto/core/naming/>

    SELECT DISTINCT ?snomedId
WHERE {
  {
    SELECT DISTINCT ?concept (STR(?name) as ?name)
    WHERE {
    
      ?concept naming:hasNaming/naming:hasName ?theName .
      ?theName ?property ?name .
      ?name bif:contains "'%s'" .
FILTER (?property IN (<https://w3id.org/hacid/onto/meta-inventory/normForm> , naming:lexicalItem))

    }
  }
  FILTER(LCASE(STR(?name)) = '%s') .
  BIND(REPLACE(STR(?concept), "https://w3id.org/hacid/mdx/data/", "") as ?snomedId) .
}
    """%(variable[0], variable[1])
    )
    
    try:
        ret = sparql.queryAndConvert()

        for r in ret["results"]["bindings"]:
            
            return r['snomedId']['value']
    except Exception as e:
        #print(e)
        return None
    
 #Normalizer   
def normCMA (term):
    url = 'http://localhost:6666/normalizer/normalize?keepOrder=true'
    datas = {"text":term}
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url, json=datas, headers=headers)
    return (r.json())


# Embedding
def embed(query):
    base_url = 'http://minsky.istc.cnr.it:4321/search'
    params = {
        'query': query,
        'limit': 1
    }
    headers = {
        'accept': 'application/json'
    }
    response = requests.get(base_url, headers=headers, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        return [response.json()['results'][0]['entity']['sctid']] # Return id if successfull
        #return response.json()
    else:
        return {'error': f'Failed to fetch data: {response.status_code}'}
    

# Matching Algorithm
def CMA (term):
    norms = normCMA(term)
    output = list(set([linkingCMA(norm) for norm in norms]))
    results = output if output[0] is not None else embed(norms)
    #print(results)
    return results