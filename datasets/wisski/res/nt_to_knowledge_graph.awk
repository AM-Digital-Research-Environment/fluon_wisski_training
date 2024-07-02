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
FNR == 1 { ++fIndex 
n=split(FILENAME,fnarray,"/")
file=fnarray[n]
}
file == "filter_predicates" { # to prevent breakage through empty files
  filter_predicates[$0];next
} 
file == "filter_relations"{
  filter_relations[$0];next
}
fIndex == 3 {
  #if ( $3 ~ /"/ ) next; # only for triples where the object isn't some string
  if ( $1 in filter_predicates ) next; # filter predicates and relations
  if ( $2 in filter_relations ) next;
  if ( $3 in filter_predicates ) next;
  
  entity_counter_out[$1] += 1
  entity_counter_in[$3] += 1
  next
}
fIndex == 4 {
  #if ( $1 ~ /http:\/\/www.wisski.uni-bayreuth.de\/wisski\/navigate\// ){
  if ( $1 ~ /http(s)?:\/\/[^\/]+\/wisski\/navigate\// ){
    id = "<"gensub(/\r$/,"","g",$1)">"
    if (!(id in ent)){
      ent[id]=n_ent
      items[id]=n_ent
      print n_ent, id >> ent_file
      print n_ent, id, gensub(/.*navigate\/([[:digit:]]+)\/view.*/,"\\1", "g", id) >> itm_file
      n_ent++
    }
  }
}
fIndex == 5 {
  if ( $3 ~ /"/ ) next; # only for triples where the object isn't some stupid string
  if ( $1 in filter_predicates ) next; # filter predicates and relations
  if ( $2 in filter_relations ) next;
  if ( $3 in filter_predicates ) next;
  # filter out things with out-degree of at least min_degree_out, but keep all items!
  if ( !($1 in items) && (entity_counter_out[$1] < min_degree_out) ) next;
  # filter out things with in-degree of at least min_degree_in, but keep all items!
  if ( !($1 in items) && (entity_counter_in[$3] < min_degree_in) ) next;

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
