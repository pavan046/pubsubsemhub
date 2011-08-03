import sparql_connect
connect=sparql_connect.VirtuosoConnect()
subscribers=connect.select("""select ?callback where {?s <http://www.w3.org/ns/auth/cert#hex> ?callback .}""")
print subscribers[0]
