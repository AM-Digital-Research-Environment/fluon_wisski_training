FNR == 1 {
	++fIndex
	n = split(FILENAME, fnarray, "/")
	file = fnarray[n]
}

file == "items_id.txt" {	# to prevent breakage through empty files
	item[$1] = $3
	next
}

file == "user_ids.tsv" {
	if (FNR > 1) {
		user[FNR - 2] = $1
	}
}

fIndex == 3 {
	FS = ","
	if ($1 in user && $2 in item) {
		print user[$1], item[$2], $3
	}
}
