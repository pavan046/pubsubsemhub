#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
from SPARQLWrapper import SPARQLWrapper, JSON, XML, N3, RDF


"""This class is built on the sparql wrapper which queries a sparql endpoint
   The returned results are then parsed based on the content type returned """
   #TODO: 1. The graph should be initialized onlu once since we will be workin
   #         on a single graph
   

class VirtuosoConnect:
    
    """This function executes a select sparql query and returns a wrapper object
    The wrapper object can later be converted to get any format of result needed"""
    def select(self, query):
    	sparql = SPARQLWrapper("http://localhost:8890/sparql")
    	sparql.setQuery(query)
    	return sparql
    	
    """This function takes in a insert statment and returns 
    whether it was executed fine or not"""
    def insert(self, insQuery): 	
    	print insQuery
        sparql = SPARQLWrapper("http://localhost:8890/sparql")
        sparql.setQuery("""
           	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        	INSERT DATA 
        	INTO <http://localhost:8890/DAV/home/smob>
        	{ <s> <p> <q> }
    	""")
        results=sparql.query().convert()
            
    def returnJson(self, wrapper):
    	uris = []
    	wrapper.setReturnFormat(JSON)
    	results = wrapper.query().convert()
    	for result in results["results"]["bindings"]:
    		uris.append(result["s"]["value"])
    	return uris
