#!/bin/bash
set -ueo pipefail

CUR=$(pwd)
DATE=$(python getDateLastDump.py)
DOWN=/projects/wikidata
CONFJSON="../allbios.json"

cd $DOWN

checkmd5=$(find . -type f -name "*md5sums.txt"|wc -l)
#echo ${checkmd5}

if [[ ${checkmd5} -gt 0 ]]; then
	rm *md5sums.txt
fi
wget -c https://dumps.wikimedia.org/wikidatawiki/entities/$DATE/wikidata-$DATE-md5sums.txt -o /dev/null

cat *md5sums.txt | grep 'json.gz' > md5sum.txt

checkjson=$(find . -type f -name "*json.gz"|wc -l)

if [[ ${checkjson} -gt 0 ]]; then
	rm *-all.json.gz
fi
wget -c -t 10 https://dumps.wikimedia.org/wikidatawiki/entities/$DATE/wikidata-$DATE-all.json.gz -o /dev/null

md5sum --strict -c md5sum.txt

status=$?

if test $status -eq 0
then
	# Process file
	cd $CUR; python autoritiesCheck.py -config ${CONFJSON} -authorities conf/autoritats.tsv -dump $DOWN/wikidata-$DATE-all.json.gz
	cd $CUR; python autStats.py -config ${CONFJSON}
	cd $CUR; python autStats.py -config ${CONFJSON} -specific dones
else
	exit 1
fi
