#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import pandas as pd
import numpy as np
import io
from urllib.parse import unquote
from urllib import request
import argparse
import pprint
import json
import mwclient
import MySQLdb
import time

pp = pprint.PrettyPrinter(indent=4)

# Import JSON configuration
parser = argparse.ArgumentParser(description="""Script for generating authority stats""")
parser.add_argument("-config",help="""Path to a JSON file with configuration options!""")
args = parser.parse_args()

host = "ca.wikipedia.org"
user = None
password = None
protocol = "https"
data = {}
targetpage = "User:Toniher/Autoritats"

conn = None

if "config" in args:
		if args.config is not None:
				with open(args.config) as json_data_file:
						data = json.load(json_data_file)

if "mw" in data:
		if "host" in data["mw"]:
				host = data["mw"]["host"]
		if "user" in data["mw"]:
				user = data["mw"]["user"]
		if "password" in data["mw"]:
				pwd = data["mw"]["password"]
		if "protocol" in data["mw"]:
				protocol = data["mw"]["protocol"]

if "mysql" in data:
	conn = MySQLdb.connect(host=data["mysql"]["host"], user=data["mysql"]["user"], passwd=data["mysql"]["password"], db=data["mysql"]["database"], use_unicode=True, charset='utf8mb4', init_command='SET NAMES utf8mb4')

if "targetpage" in data:
		targetpage = data["targetpage"]

site = mwclient.Site(host, scheme=protocol)
if user and pwd :
		# Login parameters
		site.login(user, pwd)

if conn is None:
	print("CONNECTION PROBLEM")
	exit()

cur = conn.cursor()



def printToWiki( toprint, site, targetpage ):

	text = toprint

	#page = site.pages[ targetpage ]
	#page.save( text, summary='Bios', minor=False, bot=True )

	return True

# Get all bios
bios = pd.read_sql_query("SELECT w.id as id, w.article as article from `bios` b, `wikidata` w where b.article=w.article", conn)

# Plantilla whatlinks
planaut = pd.read_sql_query("SELECT w.id as id, w.article as article from `whatlinks` l, `wikidata` w where l.article=w.article and l.against='Plantilla:Autoritat'", conn)

# Entrades amb autoritat
aut = pd.read_sql_query("SELECT a.id as id, a.authority as authority, t.name as name, t.authtype as authtype from `authorities` a, `wikidata` w, `authtypes` t where a.id=w.id and a.authority=t.prop", conn)

# Entrades amb registres
aut_rg = aut[aut.authtype.eq(1)]
# Entres amb bases d'informació
aut_bd = aut[aut.authtype.eq(2)]

aut_rg_bd = aut_rg[aut_rg.id.isin( aut_bd.id.unique() ) ]


bios_count = bios.shape[0]

# Bios with authority
bios_aut = bios[bios.id.isin(aut.id.unique())]

# Bios without authority
bios_noaut = bios[~bios.id.isin(aut.id.unique())]

# Bios without bd
bios_nobd = bios[~bios.id.isin(aut_bd.id.unique())]


aut_freq = aut.name.value_counts()
aut_id_freq = aut.groupby(by='id', as_index=False).agg({'name': pd.Series.nunique})
aut_id_freq.columns = ['id', 'count']
aut_id_freq = aut_id_freq.reset_index()

aut_id_freq_autcount = aut_id_freq["count"].value_counts()
aut_id_freq_aut1 = aut_id_freq[aut_id_freq["count"].eq(1)]

# Prepare text
text = "== General de biografies ==\n\n"

text = text + "* Total: " + str( bios_count ) + "\n"

# Stats
# * Total amb registres Autoritat i bases
aut_count = aut.id.nunique()
text = text + "** Amb autoritats: " + str( aut_count ) + "\n"

# * Total amb registres Autoritat
aut_rg_count = aut_rg.id.nunique()
text = text + "** Amb registres de control: " + str( aut_rg_count ) + "\n"

# * Total amb bases d'informació
aut_bd_count = aut_bd.id.nunique()
text = text + "** Amb bases d'informació: " + str( aut_bd_count ) + "\n"

# * Total amb registres autoritat i bases
aut_rg_bd_count = aut_rg_bd.id.nunique()
text = text + "** Amb registres de control i també bases d'informació: " + str( aut_rg_bd_count ) + "\n"

# * Total amb registre i sense base
text = text + "** Amb registres de control però sense bases d'informació: " + str( aut_rg_count - aut_rg_bd_count ) + "\n"

# * Total amb bases i sense registre
text = text + "** Sense registres de control però amb bases d'informació: " + str( aut_bd_count - aut_rg_bd_count ) + "\n"

# * Recompte per cada diferent propietat
print( aut_freq )
# * Pàgines segons nombre de propietats
print( aut_id_freq_autcount )

# Seguiment
# * Pagines només amb 1
aut_id_freq_aut1_count = aut_id_freq_aut1.id.nunique()
print( aut_id_freq_aut1_count )
# * Pàgines només amb 1 segons propietat
aut_id_freq_aut1_freq = aut[ aut.id.isin( aut_id_freq_aut1.id.unique() ) ]["name"].value_counts()
print( aut_id_freq_aut1_freq )

# Posem en pàgines el de sota
aut_orcid = aut[aut.name.eq("ORCID")]
aut_viaf = aut[aut.name.eq("VIAF")]
aut_cantic = aut[aut.name.eq("CANTIC")]
aut_bne = aut[aut.name.eq("BNE")]

# * Pàgines només amb ORCID
aut_orcid1 = aut_orcid[aut_orcid.id.isin( aut_id_freq_aut1.id.unique() )]

# * Pàgines només amb VIAF
aut_viaf1 = aut_viaf[aut_viaf.id.isin( aut_id_freq_aut1.id.unique() )]

# * Pàgines només amb CANTIC
aut_cantic1 = aut_cantic[aut_cantic.id.isin( aut_id_freq_aut1.id.unique() )]

# * Pàgines només amb BNE
aut_bne1 = aut_bne[aut_bne.id.isin( aut_id_freq_aut1.id.unique() )]

text = text + "== Plantilla d'autoritat==\n\n"

planaut_count = planaut.shape[0]

text = text + "=== Plantilla inclosa ===\n\n"

text = text + "* Nombre d'articles: " + str( planaut_count ) + "\n"

# * Total amb plantilla Autoritat
# Amb algun registre
planaut_aut = planaut[ planaut.id.isin(aut.id.unique()) ]

text = text + "** Amb autoritats: " + str( planaut_aut.shape[0] )

# Sense registre
planaut_naut = planaut[ ~planaut.id.isin(aut.id.unique()) ]
text = text + "** Sense autoritats: " + str( planaut_naut.shape[0] )

# Sense base d'informació
planaut_nbd = planaut[ ~planaut.id.isin(aut_bd.id.unique()) ]
text = text + "*** Sense bases d'informació: " + str( planaut_nbd.shape[0] )

text = text + "=== Plantilla no inclosa ===\n\n"

# Amb algun registre
noplanaut_aut = aut[ ~aut.id.isin( planaut.id.unique() ) ]
text = text + "** Amb autoritats: " + str( noplanaut_aut.shape[0] )
noplanaut_bd = aut_bd[ ~aut_bd.id.isin( planaut.id.unique() ) ]

text = text + "*** Amb bases d'informació: " + str( noplanaut_bd.shape[0] )

# Sense cap registre
noplanaut_bios = bios_noaut[ ~bios_noaut.id.isin( planaut.id.unique() ) ]
text = text + "** Sense autoritats: " + str( noplanaut_bios.shape[0] )


print( text )
