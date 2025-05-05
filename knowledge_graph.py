import hashlib
from typing import Optional, Set, Iterable

import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, Namespace, Dataset, URIRef, RDF, RDFS, Literal, XSD
from requests.auth import HTTPBasicAuth
import logging
#from collections.abc import Iterable

from slugify import slugify

LOGGER = logging.getLogger(__name__)

MDX = Namespace('https://w3id.org/hacid/onto/mdx/')
MDXD = Namespace('https://w3id.org/hacid/mdx/data/')
TOP = Namespace('https://w3id.org/hacid/onto/top-level/')
JDG = Namespace('https://w3id.org/hacid/onto/core/judgement/')
NM = Namespace('https://w3id.org/hacid/onto/core/naming/')
MI = Namespace('https://w3id.org/hacid/onto/meta-inventory/')
EV = Namespace('https://w3id.org/hacid/onto/core/evidence/')


def generate_hash_id(string: str) -> str:
    hash = hashlib.md5(string.encode())
    return hash.hexdigest()


class GraphStore(object):

    def __init__(self):
        self.__dataset = Dataset()

    def get_dataset(self) -> Dataset:
        return self.__dataset

    def create_named_graph(self, graph_identifier: URIRef) -> Graph:
        named_graph = self.__dataset.graph(graph_identifier)
        return named_graph

    def add_named_graph(self, graph: Graph, graph_identifier: URIRef) -> None:
        named_graph = self.__dataset.graph(graph_identifier)
        for s, p, o in graph:
            named_graph.add((s, p, o))

    def get_named_graph(self, graph_identifier: URIRef) -> Optional[Graph]:
        return self.__dataset.get_graph(graph_identifier)

    def serialize(self, format: str = 'nquads', destination: Optional[str] = None):
        return self.__dataset.serialize(destination=destination, format=format)


class KgClient:
    """
    A client for accessing the HACID Knowledge Graph.
    """

    def __init__(self,
                 endpoint_url: str = "https://semantics.istc.cnr.it/hacid/sparql",
                 username: str = None,
                 password: str = None):
        """
        Initialize the SPARQL client with an endpoint URL.
        """
        self.endpoint_url = endpoint_url
        self.sparql = SPARQLWrapper(endpoint_url)

        if username and password:
            self.sparql.setCredentials(username, password)

    def query(self, sparql_query: str) -> dict:
        """
        Execute a SPARQL query and return results as a dictionary.

        :param sparql_query: SPARQL query string
        :return: Query result as a dictionary
        """
        self.sparql.setQuery(sparql_query)
        self.sparql.setReturnFormat(JSON)

        try:
            return self.sparql.queryAndConvert()
        except Exception as e:
            LOGGER.error(f"SPARQL query error: {e}")
            raise RuntimeError(f"SPARQL query execution failed: {e}")

    def ask(self, sparql_query: str) -> bool:
        """
        Execute a SPARQL ASK query and return a boolean result.

        :param sparql_query: SPARQL ASK query string
        :return: Boolean result of the ASK query
        """
        self.sparql.setQuery(sparql_query)
        self.sparql.setReturnFormat(JSON)

        try:
            result = self.sparql.queryAndConvert()
            return result.get("boolean", False)
        except Exception as e:
            LOGGER.error(f"SPARQL ASK query error: {e}")
            raise RuntimeError(f"SPARQL ASK query execution failed: {e}")

    def get_broader_concepts(self, sctid: str) -> Set[str]:
        """
        Retrieves the broader (more general) concept identifiers for a given SCTID
        (SNOMED CT Identifier).

        Args:
            sctid (str): The SNOMED CT concept ID whose broader concepts are to be retrieved.

        Returns:
            set[str]: A set of broader concept IDs as strings.
        """
        query = f"""
          PREFIX mdx: <https://w3id.org/hacid/onto/mdx/>
           
          SELECT DISTINCT ?broaderId
          WHERE {{
            <https://w3id.org/hacid/mdx/data/{sctid}> mdx:broader ?broader .
            BIND(REPLACE(STR(?broader), "https://w3id.org/hacid/mdx/data/(\\\\d+)", "$1") as ?broaderId) .
          }}
        """
        results = self.query(query)

        broader_ids = set()
        for result in results["results"]["bindings"]:
            broader_ids.add(result['broaderId']['value'])

        return broader_ids

    def get_narrower_concepts(self, sctid: str) -> Set[str]:
        """
        Retrieves the narrower (more specific) concept identifiers for a given SCTID
        (SNOMED CT Identifier).

        Args:
            sctid (str): The SNOMED CT concept ID whose narrower concepts are to be retrieved.

        Returns:
            set[str]: A set of narrower concept IDs as strings.
        """
        query = f"""
          PREFIX mdx: <https://w3id.org/hacid/onto/mdx/>

          SELECT DISTINCT ?narrowerId
          WHERE {{
            ?narrower mdx:broader <https://w3id.org/hacid/mdx/data/{sctid}> .
            BIND(REPLACE(STR(?narrower), "https://w3id.org/hacid/mdx/data/(\\\\d+)", "$1") as ?narrowerId) .
          }}
        """
        results = self.query(query)

        broader_ids = set()
        for result in results["results"]["bindings"]:
            broader_ids.add(result['narrowerId']['value'])

        return broader_ids

    def get_related_concepts(self, sctid: str) -> Set[str]:
        query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX mdx: <https://w3id.org/hacid/onto/mdx/>

            SELECT DISTINCT ?otherEntityId
            WHERE {{
                <https://w3id.org/hacid/mdx/data/{sctid}> mdx:isDescribedBy ?desc .
                ?desc ?property ?otherEntity .
                ?otherEntity a ?otherEntityClass ; 
                             mdx:fullySpecifiedName [] .
            FILTER (REGEX(str(?property), "https://w3id.org/hacid/onto/mdx/.+"))
            #FILTER (?otherEntityClass in (mdx:Disorder, mdx:ClinicalFinding, mdx:Substance, mdx:Organism, mdx:MorphologicallyAbnormalStructure))
            BIND(REPLACE(STR(?otherEntity), "https://w3id.org/hacid/mdx/data/(\\\\d+)", "$1") as ?otherEntityId) .
            }}
        """

        results = self.query(query)

        concept_ids = set()
        for result in results["results"]["bindings"]:
            concept_ids.add(result['otherEntityId']['value'])

        return concept_ids

    #@staticmethod
    def write_relevance_triples(case_uri: str, entity_mention: str, sctids: Iterable[str], relevance: float, method: str) -> None:
        sctids_clean = {sctid for sctid in sctids if sctid}
        graph = GraphStore().create_named_graph(MDXD['graph/relevance'])
        for sctid in sctids_clean:
            # relevance assignment
            rel_assignment_id = generate_hash_id(f'{case_uri}-{sctid}-{relevance}')
            rel_assignment_uri = MDXD[f'relevanceassignment/{rel_assignment_id}']
            graph.add((rel_assignment_uri, RDF.type, JDG['RelevanceAssignment']))
            graph.add((rel_assignment_uri, RDFS.label, Literal(f'Relevance assignment to SNOMED concept {sctid} for clinical case {case_uri} with relevance {relevance}', lang='en')))
            # snomed concept
            graph.add((rel_assignment_uri, JDG['isJudgementOn'], MDXD[sctid]))
            # clinical case
            graph.add((rel_assignment_uri, MDX['forClinicalCase'], URIRef(case_uri)))
            # relevance
            relevance_uri = MDXD[f'relevance/{relevance}']
            graph.add((relevance_uri, RDF.type, JDG['Relevance']))
            graph.add((rel_assignment_uri, JDG['hasRelevance'], relevance_uri))
            graph.add((relevance_uri, RDFS.label, Literal(f'Relevance {relevance}', lang='en')))
            # value
            value_uri = MDXD[f'value/{relevance}']
            graph.add((value_uri, RDF.type, TOP['Value']))
            graph.add((relevance_uri, TOP['hasValue'], value_uri))
            graph.add((value_uri, RDFS.label, Literal(f'Value {relevance}', lang='en')))
            graph.add((value_uri, TOP['value'], Literal(relevance, datatype=XSD.decimal)))
            # judge
            if method:
                agent_uri = MDXD[f'agent/{slugify(method)}']
                graph.add((agent_uri, RDF.type, TOP['Agent']))
                graph.add((agent_uri, RDFS.label, Literal(method, lang='en')))
                graph.add((rel_assignment_uri, MDX['hasJudge'], agent_uri))

        print(graph.serialize(format="turtle"))
        KgClient.add_to_graph(graph, 'https://semantics.istc.cnr.it/DAV/home/hacid/mdx/add-to-graph', 'hacid', 'hacid')


    @staticmethod
    def add_to_graph(graph: Graph, endpoint_url: str, username: str, password: str):
        insert_query = f'INSERT DATA {{ GRAPH {graph.identifier.n3()} {{ {graph.serialize(format="nt")} }} }}'
        response = requests.patch(endpoint_url,
                                  data=insert_query,
                                  headers={'Content-type': 'application/sparql-query'},
                                  auth=HTTPBasicAuth(username, password))

        if response.status_code != 204:
            raise Exception(f"Update failed - Status code {response.status_code}")

    @staticmethod
    def clear_relevance_graph():
        delete_query = f'WITH <https://w3id.org/hacid/mdx/data/graph/relevance> DELETE {{ ?s ?p ?o }} WHERE {{ ?s ?p ?o }}'

        response = requests.patch('https://semantics.istc.cnr.it/DAV/home/hacid/mdx/add-to-graph',
                                  data=delete_query,
                                  headers={'Content-type': 'application/sparql-query'},
                                  auth=HTTPBasicAuth( 'hacid', 'hacid'))

        if response.status_code != 204:
            raise Exception(f"Update failed - Status code {response.status_code}")



if __name__ == '__main__':

    kg = KgClient(username="hacid", password="hacid")

    print(kg.get_broader_concepts('78275009'))
    print(kg.get_narrower_concepts('78275009'))
    print(kg.get_related_concepts('78275009'))

    #KgClient.write_relevance_triples('https://w3id.org/hacid/mdx/data/clinicalcase/02d6cb624c9e48879c5c4b6ca51daf1f', 'History of Present Illness', ['422625006'], 1.0, 'RAG')

    #KgClient.clear_relevance_graph()