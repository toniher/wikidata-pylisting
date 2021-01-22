# wikidata-pylisting
Scripts per a recuperar dades de Wikidata i combinar-les amb altres API

# Instal·lació i ús

## pyenv

Install [pyenv](https://github.com/pyenv/pyenv) and a Python version if necessary:

    pyenv install 3.7.4

Install [virtualenv](https://github.com/pyenv/pyenv-virtualenv) plugin and then enable the virtual environment:

    pyenv virtualenv 3.7.4 pylisting
    pyenv shell pylisting
    pip install -r requirements.txt

## Llistat d'últimes entrades de dones

SPARQL

    SELECT ?item ?itemLabel ?article WHERE {
      ?item wdt:P31 wd:Q5.
      ?item wdt:P21 wd:Q6581072 .
      ?article schema:about ?item .
      ?article schema:isPartOf <https://ca.wikipedia.org/> .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],ca" } .
    } ORDER BY ?itemLabel

A continuació resultats per darrera creació. Màx. 50 títols per consulta

https://ca.wikipedia.org/w/api.php?action=query&prop=revisions&rvlimit=1&rvprop=timestamp&rvdir=newer&titles=A._Brun

Query:

    curl -X GET https://query.wikidata.org/sparql?query=(SPARQL) -H "Accept: text/tab-separated-values"

# Autoritats

* Dumps de Wikidata a: https://dumps.wikimedia.org/wikidatawiki/entities/

      python autoritiesCheck.py -config /home/toniher/remote-work/mediawiki/allbios.json -authorities conf/autoritats.tsv -dump /scratch/wikidata/20200727/wikidata-20200727-all.json.gz

## WhatLinks

Recupera pàgines amb plantilla autoritat:

      python whatLinksHere.py -config ../allbios.json -title  Plantilla:Autoritat


## Addició de plantilla Autoritat

      python afegeixAutoritat.py -config ../allbios.json -file llistatpagines.txt

## Consultes

* Vegeu ./queries

## Estadístiques

PER FER

* Nombre de pàgines amb registres d'autoritat respecte a les totals
* Nombre de pàgines amb o sense plantilla autoritat i amb referències o no de registres d'autoritat
* Nombre total d'usos en pàgina d'autoritats per cada autoritat ( x Autoritat, y nombre de pàgines )
* Nombre d'usos en pàgina d'autoritats per total d'usos per pàgina ( x nombre d'autoritats, y nombre de pàgines )
* En pàgines utilitzades nombre d'usos totals d'autoritat respecte a altres autoritats ( x Autoritat, y mitja-desviació )
etc.
