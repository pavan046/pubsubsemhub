import local_virtuoso_connect
connect=local_virtuoso_connect.VirtuosoConnect()
sparql=connect.select("""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                	SELECT ?s
                	FROM <http://localhost:8890/DAV/home/smob>
                	WHERE { ?s ?p ?q }""")
subscribers = connect.returnJson(sparql)
print subscribers
