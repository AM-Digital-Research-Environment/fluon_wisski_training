FNR == 1 {
	++fIndex
}

fIndex == 1 {
	item[$1] = $3
	next
}

fIndex == 2 {
	FS = ","
	if (NR > 1 && $1 in item) {
		print item[$1], $2, $3
	}
}
