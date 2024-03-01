FNR == 1 { ++fIndex }
fIndex == 1 {
  item[$1] = $3;next
}
fIndex == 2 {
  if (FNR > 1){
    user[FNR-2] = $1;
  }
}
fIndex == 3 {
  if ( $1 in user && $2 in item ) { 
    print user[$1],item[$2],$3
  }
}
