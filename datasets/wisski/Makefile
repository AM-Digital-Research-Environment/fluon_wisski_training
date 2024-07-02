BASE_URL:=http://132.180.10.177:7200
REPO:=wisski_test
AUTH:=-u admin:WissKIAI4\#

MIN_DEGREE_IN:=1
MIN_DEGREE_OUT:=1

# https://graphdb.ontotext.com/documentation/9.0/free/index.html
#~ GRAPHDB_VERSION:=9.0F
GRAPHDB_VERSION:=10.5
# https://graphdb.ontotext.com/documentation/10.6/
#~ GRAPHDB_VERSION:=10.6


test: tmp/itemlist.nt

kg: kg_final.txt

kg_final.txt: tmp/itemlist.nt tmp/statements.nt
	awk -v OFS=' ' -v outdir='.' -v min_degree_in=$(MIN_DEGREE_IN) -v min_degree_out=$(MIN_DEGREE_OUT) -f res/nt_to_knowledge_graph.awk res/filter_predicates res/filter_relations tmp/statements.nt tmp/itemlist.nt tmp/statements.nt > $@

test: tmp/itemlist.nt
	awk -v OFS=' ' -v outdir='.' -f res/test.awk tmp/itemlist.nt

cleanall: cleanoutput cleaninput

cleaninput:
	rm -f tmp/statements.nt tmp/itemlist.nt

cleanoutput:
	rm -f entities_id.txt
	rm -f items_id.txt
	rm -f relations_id.txt
	rm -f kg_final.txt

#https://stackoverflow.com/questions/7656425/makefile-ifeq-logical-or
ifneq (,$(filter $(GRAPHDB_VERSION),9.0F 10.5))
$(info preparing statements for $(GRAPHDB_VERSION))
tmp/statements.nt:
	curl $(AUTH) -X GET -H "Accept:application/n-triples" "$(BASE_URL)/repositories/$(REPO)/statements?infer=false" > $@
endif
ifeq ($(GRAPHDB_VERSION),10.6)
tmp/statements.nt:
	curl $(AUTH) -vvv --header 'Accept: application/n-triples' --header 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' --data-urlencode query=@res/query.sparql '$(BASE_URL)/repositories/$(REPO)' > $@
endif

tmp/itemlist.nt:
	curl $(AUTH) -vvv --data-urlencode 'query@res/fetch_items.sparql' '$(BASE_URL)/repositories/$(REPO)' > $@
