CUR=$(pwd)
DATE=$(python getDateLastDump.py)
DOWN=/projects/wikidata
CONFJSON="../allbios.json"

cd $DOWN

wget -c https://dumps.wikimedia.org/wikidatawiki/entities/$DATE/wikidata-$DATE-md5sums.txt -o /dev/null

cat *md5sums.txt | grep 'json.gz' > md5sum.txt

wget -c -t 10 https://dumps.wikimedia.org/wikidatawiki/entities/$DATE/wikidata-$DATE-all.json.gz -o /dev/null

md5sum --strict -c md5sum.txt

status=$?

if test $status -eq 0
then
	# Process file
	cd $CUR; python autoritiesCheck.py -config ${CONFJSON} -authorities conf/autoritats.tsv -dump $DOWN/wikidata-$DATE-all.json.gz
else
	exit 1
fi

