BEGIN{
  rel_file=outdir"/relations_id.txt"
  print "id", "relation" > rel_file
  ent_file=outdir"/entities_id.txt"
  print "id", "entity" > ent_file
  itm_file=outdir"/items_id.txt"
  print "id", "entity", "wisskiid" > itm_file
  n_ent=0
  n_rel=0
}
FNR == 1 { ++fIndex }
FILENAME == "filter_predicates" { # to prevent breakage through empty files
  filter_predicates[$0];next
} 
FILENAME == "filter_relations"{
  filter_relations[$0];next
} 
fIndex == 3 {
  if ( $1 ~ /https:\/\/www.wisski.uni-bayreuth.de\/wisski\/navigate\// ){
    if (!($1 in ent)){
      ent[$1]=n_ent
      print n_ent, $1 >> ent_file
      print n_ent,$1, gensub(/[^[:digit:]]/,"", "g", $1) >> itm_file
      n_ent++
    }
  }
}
fIndex == 4 {
  if ( $3 ~ /"/ ) next; # only for triples where the object isn't some stupid string
  if ( $1 in filter_predicates ) next; # filter predicates and relations
  if ( $2 in filter_relations ) next;
  if ( $3 in filter_predicates ) next;

  if (!($1 in ent)){
    ent[$1]=n_ent
    print n_ent, $1 >> ent_file
    n_ent++
  }
  
  if (!($2 in rel)){
    rel[$2]=n_rel
    print n_rel, $2 >> rel_file
    n_rel++
  }
  
  if (!($3 in ent)){
    ent[$3]=n_ent
    print n_ent, $3 >> ent_file
    n_ent++
  }
  
  print ent[$1],rel[$2],ent[$3]
}
