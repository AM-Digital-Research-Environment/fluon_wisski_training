BASE_URL:=http://132.180.10.160:7200
REPO:=data160_2021

MIN_DEGREE_IN:=2
MIN_DEGREE_OUT:=2

# https://graphdb.ontotext.com/documentation/9.0/free/index.html
GRAPHDB_VERSION:=9.0F
# https://graphdb.ontotext.com/documentation/10.6/
#GRAPHDB_VERSION:=10.6


test: tmp/itemlist.nt

kg: kg_final.txt

kg_final.txt: tmp/itemlist.nt tmp/statements.nt
	awk -v OFS=' ' -v outdir='.' -v min_degree_in=$(MIN_DEGREE_IN) -v min_degree_out=$(MIN_DEGREE_OUT) -f res/nt_to_knowledge_graph.awk res/filter_predicates res/filter_relations tmp/statements.nt tmp/itemlist.nt tmp/statements.nt > $@

cleanall: cleanoutput cleaninput

cleaninput:
	rm -f tmp/statements.nt tmp/itemlist.nt

cleanoutput:
	rm -f entities_id.txt
	rm -f items_id.txt
	rm -f relations_id.txt
	rm -f kg_final.txt

ifeq ($(GRAPHDB_VERSION),9.0F)
$(info preparing statements for $(GRAPHDB_VERSION))
tmp/statements.nt:
	curl -X GET -H "Accept:application/n-triples" "$(BASE_URL)/repositories/$(REPO)/statements?infer=false" > $@
endif
ifeq ($(GRAPHDB_VERSION),10.6)
tmp/statements.nt:
	curl -vvv --header 'Accept: application/n-triples' --header 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' --data-urlencode query=@res/query.sparql '$(BASE_URL)/repositories/$(REPO)' > $@
endif

tmp/itemlist.nt:
	curl -vvv --data-urlencode 'query@res/fetch_items.sparql' '$(BASE_URL)/repositories/$(REPO)' > $@
