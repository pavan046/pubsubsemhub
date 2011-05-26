import sparql_connect
connect=sparql_connect.VirtuosoConnect()
subscribers=connect.select("""select ?callback where {?callback <callback-of> ?user .\t?user <isfriendof> <http://localhost/smob> .}""")
print subscribers
