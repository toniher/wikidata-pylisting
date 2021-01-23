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

# Get all bios
bios = pd.read_sql_query("SELECT w.id, w.article from `bios` b, `wikidata` w where b.article=w.article", conn)

# Plantilla whatlinks
planaut = pd.read_sql_query("SELECT w.id, w.article from `whatlinks` l, `wikidata` w where l.article=w.article and l.against='Plantilla:Autoritat'", conn)

# Entrades amb autoritat
aut = pd.read_sql_query("SELECT a.id, a.authority, t.name, t.authtype from `authorities` a, `wikidata` w, `authtypes` t where a.id=w.id and a.authority=t.prop", conn)


# TODO:
# Stats
# * Total amb registres Autoritat
# * Total amb bases d'informació
# * Total amb registres autoritat i bases
# * Total amb bases i sense registre
# * Total amb registre i sense base
# * Total amb plantilla Autoritat (amb algun registre, sense, autoritat, informació)
# * Total sense plantilla Autoritat (amb algun registre, sense, autoritat, informació)
# * Recompte per cada diferent propietat
# * Pàgines segons nombre de propietats
# Seguiment
# * Pàgines només amb ORCID
# * Pàgines només amb VIAF
# * Pàgines només amb CANTIC
# * Pàgines només amb BNE


def printToWiki( toprint, site, targetpage ):

        text = toprint

		#page = site.pages[ targetpage ]
		#page.save( text, summary='Bios', minor=False, bot=True )

		return True
