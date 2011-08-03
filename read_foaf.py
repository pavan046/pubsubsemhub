import logging
import rdflib
import sparql_connect

# Configure how we want rdflib logger to log messages
_logger = logging.getLogger("rdflib")
_logger.setLevel(logging.DEBUG)
_hdlr = logging.StreamHandler()
_hdlr.setFormatter(logging.Formatter('%(name)s %(levelname)s: %(message)s'))
_logger.addHandler(_hdlr)

from rdflib.graph import Graph
from rdflib.term import URIRef, Literal, BNode
from rdflib.namespace import Namespace, RDF
from rdflib import plugin

HUB_CERTIFICATE = 'hub_cert.pem'
HUB_KEY = 'hub_key.key'
subscriber_private_uri = "http://localhost/smob/private"


import urllib2, httplib
import cookielib

#Add Namespaces here to use it through out the file
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
PUSH = Namespace("http://vocab.deri.ie/push/")
        
        
class ReadFOAF:
    """
        @author: Pavan Kapanipathi#
        class ReadFOAF: This class reads a foaf profile provided the source.
                Adds the required triples(publisher/subscriber) to the FOAF profile.
                Transforms the RDF/XML to tuple format, convinient to store it via sparql endpoint 
    """
    
    def __init__(self):
        self.triple_store = sparql_connect.VirtuosoConnect()
        plugin.register('sparql', rdflib.query.Processor,
                        'rdfextras.sparql.processor', 'Processor')
        plugin.register('sparql', rdflib.query.Result,
        	    'rdfextras.sparql.query', 'SPARQLQueryResult')
        
    def parsefoaf(self, location, pub, topic, callback):
        """
         Method: parsefoaf(location)
         @param location:Either the location or the foaf profile as a string
         Parses the foaf profile and provides the URI of the person who is represented in the FOAF
         Returns graph, person's uri
         
         TODO: Before the foaf triples are sent, need to check whether the publisher or the 
               subscriber are already in the rdf store.
                
        """
        store = Graph()
        store.bind("dc", "http://http://purl.org/dc/elements/1.1/")
        store.bind("foaf", "http://xmlns.com/foaf/0.1/")
        foaf = get_private_uri(location, HUB_CERTIFICATE, HUB_KEY)
        store.parse(data=foaf, format="application/rdf+xml")
		#store.parse("http://www.w3.org/People/Berners-Lee/card.rdf")
		#for person in store.subjects(RDF.type, FOAF["Person"]):
		     #print "Person:"+person
        qres = store.query(
		    """SELECT DISTINCT ?a 
		       WHERE {
			  ?a a <http://xmlns.com/foaf/0.1/Person> .
			  ?b <http://xmlns.com/foaf/0.1/primaryTopic> ?a .
		       }""")
        person_URI = ''
        for row in qres.result:
		     person_URI = row
        # Check whether the foaf of the person is already present in the rdf store.
        # To speed up the execution we can keep a cache of the person_URIs whose foaf profiles 
        # are present.
        logging.info("Checking whether foaf: %s is already present in the RDF store", person_URI)
        if self.triple_store.foaf_exists(person_URI):
            store = Graph()
            logging.info("foaf: %s is already present in the RDF store", person_URI)
        # Add the rest of the required triples to the graph
        store = self.addTriples(store, person_URI, pub, topic, callback)
        # Transform the graph to triples 
        triples = self.to_tuples(store, location)
         
        return triples
    
    def addTriples(self, graph, uri, pub, topic, callback):
        """ Method: addTriples(graph, uri, pub, topic)
            @param graph: profile in the graph format
            uri: URI of the person who is represented in the FOAF profile
            pub: boolean whether he is a publisher or not
            topic: topic URL publishing/subscribing
            Add the corresponding triples based on the PUSH vocabulary
            Returns graph 
        """
        smobAccount = uri+"-smob"
        graph.add((URIRef(uri), FOAF["holdsAccount"], URIRef(smobAccount)))
        if pub:
            graph.add((URIRef(topic), PUSH["has_owner"], URIRef(smobAccount)))
            logging.info("Adding triples to Publisher %s", uri)
        else:
            graph.add((URIRef(uri), PUSH["has_callback"], URIRef(callback)))
            graph.add((URIRef(topic), PUSH["has_subscriber"], URIRef(smobAccount)))
            logging.info("Adding triples to Subscriber %s", uri)
        return graph

		#store.serialize("foaf.rdf", format="pretty-xml", max_depth=3)
    
    def to_tuples(self, graph, location):
        """
        Method: to_tuples(graph)
        @param graph:the graph which has to be converted to tuples
        Returns array of triples which can be Inserted via a sparql endpoint
        """
        logging.info("Transforming the graph with PUSH triples for %s", location)
        triples = []
        for s, o, p in graph:
            triple = []
            if s.__class__ is BNode:
				triple.append('_:'+str(s))
            else:
                if len(str(s))==0:
                    s = location
                triple.append('<'+str(s)+'>')
            triple.append('<'+str(o)+'>')
            if p.__class__ is BNode:
                triple.append('_:'+str(p))
            elif p.__class__ is URIRef:
				triple.append('<'+str(p)+'>')
            else:
            	triple.append('"""'+str(p)+'"""')
            triples.append(triple)
        return triples
                        	

		
		
class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
  # http://www.osmonov.com/2009/04/client-certificates-with-urllib2.html
  def __init__(self, key, cert):
    urllib2.HTTPSHandler.__init__(self)
    self.key = key
    self.cert = cert
  def https_open(self, req):
    return self.do_open(self.getConnection, req)
  def getConnection(self, host, timeout=300):
    return httplib.HTTPSConnection(host, key_file=self.key, cert_file=self.cert)

def get_private_uri(uri, cert, key):
  """Request a URI that requires a client certificate

  Args:
    uri: The URI string to request.
    cert: The x509 client certificate file path
    key: the certificate key file path

  Returns:
    An ascii string with the response.
  """
  cj = cookielib.LWPCookieJar()
  opener = urllib2.build_opener(HTTPSClientAuthHandler(key, cert), urllib2.HTTPCookieProcessor(cj))
  response = opener.open(uri)
  return response.read()


def main():
	read = ReadFOAF()
	triples = read.parsefoaf("http://localhost/smob/private", True, "http://topic.com/semanticweb", "")
        for row in triples:
            print row[0]+' '+row[1]+' '+row[2]+' .'
	#for s, o, p in store:
	#	if p.__class__ is BNode:
	#		print p
	#	print s+'\t'+p+'\t'+q
	#print store
    #     store.serialize(format='pretty-xml')
    #for statement in store:
        #print statement
    

if __name__ == "__main__":
	main()
