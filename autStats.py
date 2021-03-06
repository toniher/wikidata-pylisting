#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import datetime
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
parser.add_argument("-specific",help="""Specific mode""")
args = parser.parse_args()

host = "ca.wikipedia.org"
user = None
password = None
protocol = "https"
data = {}
autpage = "User:Toniher/Autoritats"
autpagew = "Viquiprojecte:Viquidones/Autoritats"
logdir = None

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

if "autpage" in data:
	autpage = data["autpage"]

if "logdir" in data:
	logdir = data["logdir"]

site = mwclient.Site(host, scheme=protocol)
if user and pwd :
		# Login parameters
		site.login(user, pwd)

if conn is None:
	print("CONNECTION PROBLEM")
	exit()

cur = conn.cursor()


def formatWikidata(value):

	value = "[[:d:"+value+"|"+value+"]]"
	return value


def formatCawiki(value):

	text = value.replace("_", " ")
	value = "[["+value+"|"+text+"]]"
	return value


def printToWiki(toprint, site, summary, targetpage):

	text = toprint

	page = site.pages[targetpage]
	page.save(text, summary=summary, minor=False, bot=True)

	return True


def printDfoWiki(df, site, summary, targetpage):

	text = ""
	text = text + "\n{| class='wikitable sortable'\n"

	text = text + "! id !! article \n"

	for id, article in df.itertuples(index=False):
		text = text + "|-\n| " + formatWikidata(str(id)) + " || " + formatCawiki(str(article)) + "\n"

	text = text + "|}\n"

	page = site.pages[targetpage]
	page.save(text, summary=summary, minor=False, bot=True)

	return True

specific = ""

if args.specific is not None:
	specific = args.specific

storehash = dict()

extratable = ""
extrawhere = ""

if specific == "dones":
	autpage = autpagew
	extratable = ", `gender` g "
	extrawhere = " and g.id=w.id and g.gender='Q6581072'"

# Get all bios
bios = pd.read_sql_query("SELECT w.id as id, w.article as article from `bios` b, `wikidata` w "+ extratable+" where b.article=w.article "+extrawhere, conn)

# Plantilla whatlinks
planaut = pd.read_sql_query("SELECT w.id as id, w.article as article from `whatlinks` l, `wikidata` w " + extratable + " where l.article=w.article and l.against='Plantilla:Autoritat'"+extrawhere, conn)

planfva = pd.read_sql_query("SELECT w.id as id, w.article as article from `whatlinks` l, `wikidata` w " + extratable + " where l.article=w.article and l.against='Plantilla:Falta_verificar_admissibilitat'"+extrawhere, conn)

plannrf = pd.read_sql_query("SELECT w.id as id, w.article as article from `whatlinks` l, `wikidata` w " + extratable + " where l.article=w.article and l.against='Plantilla:Falten_referències'"+extrawhere, conn)

# Entrades amb autoritat
aut = pd.read_sql_query("SELECT a.id as id, a.authority as authority, t.name as name, t.authtype as authtype from `authorities` a, `wikidata` w, `authtypes` t" + extratable +" where a.id=w.id and a.authority=t.prop"+extrawhere, conn)

# Entrades amb registres
aut_rg = aut[aut.authtype.eq(1)]
# Entres amb bases d'informació
aut_bd = aut[aut.authtype.eq(2)]

aut_rg_bd = aut_rg[aut_rg.id.isin(aut_bd.id.unique())]


bios_count = bios.shape[0]
storehash["bios_count"] = bios_count

# Bios with authority
bios_aut = bios[bios.id.isin(aut.id.unique())]
storehash["bios_aut_count"] = bios_aut.shape[0]

# Bios without authority
bios_noaut = bios[~bios.id.isin(aut.id.unique())]
storehash["bios_noaut_count"] = bios_noaut.shape[0]

# Bios without bd
bios_nobd = bios[~bios.id.isin(aut_bd.id.unique())]
storehash["bios_nobd_count"] = bios_nobd.shape[0]

# Bios with bd
bios_bd = bios[bios.id.isin(aut_bd.id.unique())]
storehash["bios_bd_count"] = bios_bd.shape[0]

aut_freq = aut.name.value_counts()
aut_id_freq = aut.groupby(by='id', as_index=False).agg({'name': pd.Series.nunique})
aut_id_freq.columns = ['id', 'count']
aut_id_freq = aut_id_freq.reset_index()

aut_id_freq_autcount = aut_id_freq["count"].value_counts()
aut_id_freq_aut1 = aut_id_freq[aut_id_freq["count"].eq(1)]

nota = """IMPORTANT: Els nombres són aproximats, perquè les fonts d'autoritats (recollides processant Wikidata)
no s'actualitzen tant sovint com la resta de fonts (biografies de Wikidata i pàgines amb plantilla d'autoritats)."""

text = nota + "\n\n"

# Prepare text
text = text + "== General de biografies ==\n\n"

text = text + "* Total: " + str(bios_count) + "\n"

# Stats
# * Total amb registres Autoritat i bases
aut_count = aut.id.nunique()
storehash["aut_count"] = aut_count
text = text + "** Amb autoritats: " + str(aut_count) + "\n"

# * Total amb registres Autoritat
aut_rg_count = aut_rg.id.nunique()
storehash["aut_rg_count"] = aut_rg_count
text = text + "*** Amb registres de control: " + str(aut_rg_count) + "\n"

# * Total amb registres autoritat i bases
aut_rg_bd_count = aut_rg_bd.id.nunique()
storehash["aut_rg_bd_count"] = aut_rg_bd_count
text = text + "**** Amb registres de control i també bases d'informació: " + str(aut_rg_bd_count) + "\n"

# * Total amb registre i sense base
text = text + "**** Amb registres de control però sense bases d'informació: " + str(aut_rg_count - aut_rg_bd_count) + "\n"

# * Total amb bases d'informació
aut_bd_count = aut_bd.id.nunique()
storehash["aut_bd_count"] = aut_bd_count
text = text + "*** Amb bases d'informació: " + str(aut_bd_count) + "\n"

# * Total amb bases i sense registre
text = text + "**** Amb bases d'informació però sense registres de control: " + str(aut_bd_count - aut_rg_bd_count) + "\n"

text = text + "== Recompte per autoritats ==\n\n"

text = text + "=== Nombre d'autoritats ===\n"
# * Recompte per cada diferent propietat
# print(aut_freq)
text = text + "\n{| class='wikitable sortable'\n"

chartx = []
charty = []
text = text + "! Autoritat !! Recompte \n"
for idx, val in aut_freq.iteritems():
	chartx.append(idx)
	charty.append(str(val))
	storehash["aut_idx_" + idx] = val
	text = text + "|-\n| " + idx + " || " + str(val) + "\n"

text = text + "|}\n"

text = text + "{{Graph:Chart|width=600|height=200|type=rect|xAxisAngle = -40|x="+",".join(chartx)+"|y="+",".join(charty)+"|showValues=}}\n"
# * Pàgines segons nombre de propietats

text = text + "=== Nombre d'autoritats diferents per pàgina ===\n"

chartx = []
charty = []
chartxy = {}
text = text + "\n{| class='wikitable sortable'\n"

text = text + "! Nombre d'autoritats !! Pàgines \n"
for idx, val in aut_id_freq_autcount.iteritems():
	chartxy[str(idx)] = str(val)
	chartx.append(idx)
	storehash["aut_num_" + str(idx)] = val
	text = text + "|-\n| " + str(idx) + " || " + str(val) + "\n"

text = text + "|}\n"

chartx.sort()
for i in chartx :
	charty.append(chartxy[str(i)])

text = text + "{{Graph:Chart|width=600|height=200|type=rect|x="+",".join(map(lambda x: str(x), chartx))+"|y="+",".join(charty)+"|showValues=}}\n"

text = text + "\n=== Pàgines només amb 1 autoritat ===\n\n"

# Seguiment
# * Pagines només amb 1
aut_id_freq_aut1_count = aut_id_freq_aut1.id.nunique()
text = text + "Nombre: " + str(aut_id_freq_aut1_count)

# * Pàgines només amb 1 segons propietat
aut_id_freq_aut1_freq = aut[aut.id.isin(aut_id_freq_aut1.id.unique())]["name"].value_counts()

text = text + "\n{| class='wikitable sortable'\n"

text = text + "! Autoritat !! Recompte \n"
for idx, val in aut_id_freq_aut1_freq.iteritems():
	text = text + "|-\n| " + idx + " || " + str(val) + "\n"

text = text + "|}\n"

text = text + "\n== Plantilla d'autoritat==\n\n"

planaut_count = planaut.shape[0]
storehash["planaut_count"] = planaut_count

text = text + "\n=== Plantilla inclosa ===\n\n"

text = text + "* Nombre d'articles: " + str(planaut_count) + "\n"

# * Total amb plantilla Autoritat
# Amb algun registre
planaut_aut = planaut[planaut.id.isin(aut.id.unique())]

storehash["planaut_aut_count"] = planaut_aut.shape[0]
text = text + "** Amb autoritats: " + str(planaut_aut.shape[0]) + "\n"

# Sense registre
planaut_naut = planaut[~planaut.id.isin(aut.id.unique())]
storehash["planaut_naut_count"] = planaut_naut.shape[0]
text = text + "** Sense autoritats: " + str(planaut_naut.shape[0]) + "\n"

# Sense base d'informació
planaut_nbd = planaut[~planaut.id.isin(aut_bd.id.unique())]
storehash["planaut_nbd_count"] = planaut_nbd.shape[0]
text = text + "** Sense bases d'informació: " + str(planaut_nbd.shape[0]) + "\n"

text = text + "\n=== Plantilla no inclosa ===\n\n"
storehash["noplanaut_count"] = bios_count - planaut_count
text = text + "* Nombre d'articles: " + str(bios_count - planaut_count) + "\n"

# Amb algun registre
noplanaut_aut = bios_aut[~bios_aut.id.isin(planaut.id.unique())]
storehash["noplanaut_aut_count"] = noplanaut_aut.shape[0]
text = text + "** Amb autoritats: " + str(noplanaut_aut.shape[0]) + "\n"
noplanaut_bd = bios_bd[~bios_bd.id.isin(planaut.id.unique())]
storehash["noplanaut_bd_count"] = noplanaut_bd.shape[0]
text = text + "*** Amb bases d'informació: " + str(noplanaut_bd.shape[0]) + "\n"

# Sense cap registre
noplanaut_bios = bios_noaut[~bios_noaut.id.isin(planaut.id.unique())]
storehash["noplanaut_bios_count"] = noplanaut_bios.shape[0]
text = text + "** Sense autoritats: " + str(noplanaut_bios.shape[0]) + "\n"

# Plantilla falta verificar admissibilitat

text = text + "\n== Plantilla d'admissibilitat==\n\n"

planfva_count = planfva.shape[0]
storehash["planfva_count"] = planfva_count

text = text + "\n=== Plantilla inclosa ===\n\n"

text = text + "* Nombre d'articles: " + str(planfva_count) + "\n"

# * Total amb plantilla admissibilitat
# Amb algun registre
planfva_aut = planfva[planfva.id.isin(aut.id.unique())]
storehash["planfva_aut_count"] = planfva_aut.shape[0]

text = text + "** [[/Planfva_Aut|Amb autoritats]]: " + str(planfva_aut.shape[0]) + "\n"

# Amb bases d'informació
planfva_bd = planfva[planfva.id.isin(aut_bd.id.unique())]
storehash["planfva_bd_count"] = planfva_bd.shape[0]

text = text + "*** [[/Planfva_BD|Amb bases d'informació]]: " + str(planfva_bd.shape[0]) + "\n"

# Sense registre
planfva_naut = planfva[~planfva.id.isin(aut.id.unique())]
storehash["planfva_naut_count"] = planfva_naut.shape[0]

text = text + "** [[/Planfva_No_Aut|Sense autoritats]]: " + str(planfva_naut.shape[0]) + "\n"

# Sense base d'informació
planfva_nbd = planfva[~planfva.id.isin(aut_bd.id.unique())]
storehash["planfva_nbd_count"] = planfva_nbd.shape[0]

text = text + "** [[/Planfva_No_BD|Sense bases d'informació]]: " + str(planfva_nbd.shape[0]) + "\n"

# Plantilla falten referències

text = text + "\n== Plantilla de manca de referències ==\n\n"

plannrf_count = plannrf.shape[0]
storehash["plannrf_count"] = plannrf_count

text = text + "\n=== Plantilla inclosa ===\n\n"

text = text + "* Nombre d'articles: " + str(plannrf_count) + "\n"

# * Total amb plantilla Autoritat
# Amb algun registre
plannrf_aut = plannrf[plannrf.id.isin(aut.id.unique())]
storehash["plannrf_aut_count"] = plannrf_aut.shape[0]

text = text + "** [[/Plannrf_Aut|Amb autoritats]]: " + str(plannrf_aut.shape[0]) + "\n"

plannrf_bd = plannrf[plannrf.id.isin(aut_bd.id.unique())]
storehash["plannrf_bd_count"] = plannrf_bd.shape[0]

text = text + "*** [[/Plannrf_BD|Amb bases d'informació]]: " + str(plannrf_bd.shape[0]) + "\n"

# Sense registre
plannrf_naut = plannrf[~plannrf.id.isin(aut.id.unique())]
storehash["plannrf_naut_count"] = plannrf_naut.shape[0]

text = text + "** [[/Plannrf_No_Aut|Sense autoritats]]: " + str(plannrf_naut.shape[0]) + "\n"

# Sense base d'informació
plannrf_nbd = plannrf[~plannrf.id.isin(aut_bd.id.unique())]
storehash["plannrf_nbd_count"] = plannrf_nbd.shape[0]

text = text + "** [[/Plannrf_No_BD|Sense bases d'informació]]: " + str(plannrf_nbd.shape[0]) + "\n"

# Revisions diverses
# TODO: Cal fer més diverses i útils

text = text + "\n== Revisió ==\n\n"

# Posem en pàgines el de sota
# TODO: Generalitzar per tots els casos
aut_orcid = aut[aut.name.eq("ORCID")]
aut_viaf = aut[aut.name.eq("VIAF")]
aut_cantic = aut[aut.name.eq("CANTIC")]
aut_bne = aut[aut.name.eq("BNE")]

# * Pàgines només amb ORCID
aut_orcid1 = aut_orcid[aut_orcid.id.isin(aut_id_freq_aut1.id.unique())]
bios_aut_orcid1 = aut_orcid1.merge(bios_aut, how="inner", on="id")[["id", "article"]]

printDfoWiki(bios_aut_orcid1, site, "Actualització de recompte d'autoritats", autpage+"/ORCID")
text = text + "\n* [[/ORCID|ORCID per revisar]]"

# * Pàgines només amb VIAF
aut_viaf1 = aut_viaf[aut_viaf.id.isin(aut_id_freq_aut1.id.unique())]
bios_aut_viaf1 = aut_viaf1.merge(bios_aut, how="inner", on="id")[["id", "article"]]

printDfoWiki(bios_aut_viaf1, site, "Actualització de recompte d'autoritats", autpage+"/VIAF")
text = text + "\n* [[/VIAF|VIAF per revisar]]"

# * Pàgines només amb CANTIC
aut_cantic1 = aut_cantic[aut_cantic.id.isin(aut_id_freq_aut1.id.unique())]
bios_aut_cantic1 = aut_cantic1.merge(bios_aut, how="inner", on="id")[["id", "article"]]

printDfoWiki(bios_aut_cantic1, site, "Actualització de recompte d'autoritats", autpage+"/CANTIC")
text = text + "\n* [[/CANTIC|CANTIC per revisar]]"

# * Pàgines només amb BNE
aut_bne1 = aut_bne[aut_bne.id.isin(aut_id_freq_aut1.id.unique())]
bios_aut_bne1 = aut_bne1.merge(bios_aut, how="inner", on="id")[["id", "article"]]

printDfoWiki(bios_aut_bne1, site, "Actualització de recompte d'autoritats", autpage+"/BNE")
text = text + "\n* [[/BNE|BNE per revisar]]"

printDfoWiki(noplanaut_bd[["id", "article"]], site, "Actualització de recompte d'autoritats", autpage+"/Noplanaut_BD")
text = text + "\n* [[/Noplanaut BD|Amb bases d'informació i sense plantilla d'autoritat per revisar]]"

# More pages
printDfoWiki(plannrf_aut[["id", "article"]], site, "Actualització de recompte d'autoritats", autpage+"/Plannrf_Aut")
printDfoWiki(plannrf_bd[["id", "article"]], site, "Actualització de recompte d'autoritats", autpage+"/Plannrf_BD")
printDfoWiki(plannrf_naut[["id", "article"]], site, "Actualització de recompte d'autoritats", autpage+"/Plannrf_No_Aut")
printDfoWiki(plannrf_nbd[["id", "article"]], site, "Actualització de recompte d'autoritats", autpage+"/Plannrf_No_BD")

printDfoWiki(planfva_aut[["id", "article"]], site, "Actualització de recompte d'autoritats", autpage+"/Planfva_Aut")
printDfoWiki(planfva_bd[["id", "article"]], site, "Actualització de recompte d'autoritats", autpage+"/Planfva_BD")
printDfoWiki(planfva_naut[["id", "article"]], site, "Actualització de recompte d'autoritats", autpage+"/Planfva_No_Aut")
printDfoWiki(planfva_nbd[["id", "article"]], site, "Actualització de recompte d'autoritats", autpage+"/Planfva_No_BD")


print(text)
printToWiki(text, site, "Actualització de recompte d'autoritats", autpage)

# Adding in a log more info
if logdir:
	prefix = "all"
	if specific != "":
		prefix = specific
	now = datetime.now() # current date and time
	datebit = now.strftime("%Y%m%d")
	pathdir = logdir + "/" + datebit
	pathlog = pathdir + "/" + prefix + ".csv"
	if not os.path.exists(pathdir):
		os.mkdir(pathdir)
	towrite = ""
	for key in sorted(storehash):
		towrite = towrite + key + "\t" + str(storehash[key]) + "\n"
	f = open(pathlog, "w")
	f.write(towrite)
	f.close()
