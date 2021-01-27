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
# planaut = pd.read_sql_query("SELECT w.id as id, w.article as article from `whatlinks` l, `wikidata` w where l.article=w.article and l.against='Plantilla:Autoritat'", conn)

# Entrades amb autoritat
aut = pd.read_sql_query("SELECT a.id as id, a.authority as authority, t.name as name, t.authtype as authtype from `authorities` a, `wikidata` w, `authtypes` t where a.id=w.id and a.authority=t.prop", conn)

bios_count = bios.shape[0]
# planaut_count = planaut.shape[0]

biosaut = pd.merge(bios, aut, how='inner', on='id')

# Entrades amb registres
aut_rg = aut[aut.authtype.eq(1)]
# Entres amb bases d'informació
aut_bd = aut[aut.authtype.eq(2)]

aut_rg_bd = aut_rg[aut_rg.id.isin( aut_bd.id.unique() ) ]

aut_freq = aut.name.value_counts()
aut_id_freq = aut.groupby(by='id', as_index=False).agg({'name': pd.Series.nunique})
aut_id_freq.columns = ['id', 'count']
aut_id_freq = aut_id_freq.reset_index()

aut_id_freq_autcount = aut_id_freq["count"].value_counts()
aut_id_freq_aut1 = aut_id_freq[aut_id_freq["count"].eq(1)]

print( bios_count )
# print( planaut_count )

# TODO:
# Stats
# * Total amb registres Autoritat i bases
aut_count = aut.id.nunique()
print( aut_count )
# * Total amb registres Autoritat
aut_rg_count = aut_rg.id.nunique()
print( aut_rg_count )
# * Total amb bases d'informació
aut_bd_count = aut_bd.id.nunique()
print( aut_bd_count )
# * Total amb registres autoritat i bases
aut_rg_bd_count = aut_rg_bd.id.nunique()
print( aut_rg_bd_count )
# * Total amb registre i sense base
print( aut_rg_count - aut_rg_bd_count )
# * Total amb bases i sense registre
print( aut_bd_count - aut_rg_bd_count )

# * Total amb plantilla Autoritat (amb algun registre, sense, autoritat, informació)
# * Total sense plantilla Autoritat (amb algun registre, sense, autoritat, informació)
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

aut_orcid = aut[aut.name.eq("ORCID")]
aut_viaf = aut[aut.name.eq("VIAF")]
aut_cantic = aut[aut.name.eq("CANTIC")]
aut_bne = aut[aut.name.eq("BNE")]

# * Pàgines només amb ORCID
aut_orcid1 = aut_orcid[aut_orcid.id.isin( aut_id_freq_aut1.id.unique() )]
print( aut_orcid1.shape[0] )

# * Pàgines només amb VIAF
aut_viaf1 = aut_viaf[aut_viaf.id.isin( aut_id_freq_aut1.id.unique() )]
print( aut_viaf1.shape[0] )

# * Pàgines només amb CANTIC
aut_cantic1 = aut_cantic[aut_cantic.id.isin( aut_id_freq_aut1.id.unique() )]
print( aut_cantic1.shape[0] )

# * Pàgines només amb BNE
aut_bne1 = aut_bne[aut_bne.id.isin( aut_id_freq_aut1.id.unique() )]
print( aut_bne1.shape[0] )
