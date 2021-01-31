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

## A la Viquipèdia

* [Seguiment de biografies](https://ca.wikipedia.org/wiki/Usuari:Toniher/Bios)
  * [Seguiment de biografies de dones](https://ca.wikipedia.org/wiki/Viquiprojecte:Viquidones/Progr%C3%A9s)
* [Comprovacions de gènere](https://ca.wikipedia.org/wiki/Usuari:Toniher/StatsGender)
* [Problemàtiques de Wikidata i biografies](https://ca.wikipedia.org/wiki/Usuari:Toniher/CheckBios)
* [Tauler d'autoritats](https://ca.wikipedia.org/wiki/Usuari:Toniher/Autoritats)
