#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
from SPARQLWrapper import SPARQLWrapper, JSON, XML, N3, RDF

DEBUG = False


   

class VirtuosoConnect:
    """This class is built on the sparql wrapper which queries a sparql endpoint
   The returned results are then parsed based on the content type returned 
   TODO: 1. The graph should be initialized onlu once since we will be workin
            on a single graph
         2. Make this a singleton class with all the initializations done once
            """
    
    def select(self, query):
        """This function executes a select sparql query and returns a wrapper object
        The wrapper object can later be converted to get any format of result needed"""
        prefix = """PREFIX sioc: <http://rdfs.org/sioc/ns#>
                    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                    PREFIX push: <http://push.deri.ie/smob/> 
                    PREFIX purl: <http://purl.org/dc/terms/>
                    PREFIX category: <http://dbpedia.org/resource/Category:>
                 """
        query = prefix + query        
    	sparql = SPARQLWrapper("http://localhost:8890/sparql")
    	sparql.setQuery(query)
        logging.debug('Query: %r', query)
    	uris = self.returnJson(sparql, "callback")
        logging.debug('uris: %r', uris)
	return uris
    
    def foaf_exists(self, person_URI):
        """This function checks if the foaf profile of the person already present or not
            TODO: This can be done in terms of ask query which returns the JSON format"""
        query = """SELECT COUNT(*) 
               FROM <http://localhost:8890/DAV/home/smob>
               WHERE {
              <"""+ person_URI +"""> a foaf:Person .
              ?b foaf:primaryTopic <"""+ person_URI +"""> .
               }"""
        sparql = SPARQLWrapper("http://localhost:8890/sparql")
        sparql.setQuery(query)
        count_array = self.returnJson(sparql, "callret-0")
        if int(count_array[0]) > 0:
            logging.debug("count of foaf profile: %s", count_array[0])
            return True
        return False
    	
    def insert(self, insQuery):
        """This function takes in a insert statment and returns 
        whether it was executed fine or not"""
     	print "Triples: "+insQuery
    	sparql = SPARQLWrapper("http://localhost:8890/sparql")
        sparql.setQuery("""
           	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        	INSERT DATA 
        	INTO <http://localhost:8890/DAV/home/test>
        	{ """+insQuery+"""}
    	""")
        results=sparql.query().convert()
    
    def insertTriples(self, triples):
        count = len(triples)
        tripleString = ""
        for row in triples:
            tripleString += row[0]+' '+row[1]+' '+row[2]+' . '
            if count%10 == 0:
                self.insert(tripleString) 
                tripleString = ""
            count = count-1
        if tripleString is not "":
            self.insert(tripleString)
        
            
    def returnJson(self, wrapper, variable):
    	uris = []
    	wrapper.setReturnFormat(JSON)
    	results = wrapper.query().convert()
    	for result in results["results"]["bindings"]:
    		uris.append(result[variable]["value"])
    	return uris
