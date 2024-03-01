BASE_URL:=http://132.180.10.160:7200
REPO:=data160_2021

# https://graphdb.ontotext.com/documentation/9.0/free/index.html
GRAPHDB_VERSION:=9.0F
# https://graphdb.ontotext.com/documentation/10.6/
#GRAPHDB_VERSION:=10.6

kg: kg_final.txt

kg_final.txt: tmp/statements.nt
	#head -n 6 $< > tmp/st6.nt && \
	#awk -v OFS=' ' -v outdir='out' -f nt_to_knowledge_graph.awk filter_predicates filter_relations tmp/st6.nt tmp/st6.nt > $@ && rm -f tmp/st6.nt
	awk -v OFS=' ' -v outdir='out' -f res/nt_to_knowledge_graph.awk res/filter_predicates res/filter_relations $< $< > $@

cleanall: cleanoutput cleaninput

cleaninput:
	rm -f tmp/statements.nt

cleanoutput:
	rm -f entities_id.txt
	rm -f items_id.txt
	rm -f relations_id.txt
	rm -f kg_final.txt

ifeq ( $(GRAPHDB_VERSION), 9.0F)
tmp/statements.nt:
	curl -X GET -H "Accept:application/n-triples" "$(BASE_URL)/repositories/$(REPO)/statements?infer=false" > $@
endif
ifeq ( $(GRAPHDB_VERSION), 10.6)
tmp/statements.nt:
	curl -vvv --header 'Accept: application/n-triples' --header 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' --data-urlencode query=@res/query.sparql '$(BASE_URL)/repositories/$(REPO)'
endif

