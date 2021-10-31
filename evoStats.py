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
parser = argparse.ArgumentParser(description="""Script for generating evolution stats""")
parser.add_argument("-config",help="""Path to a JSON file with configuration options!""")
# parser.add_argument("-specific",help="""Specific mode""")
args = parser.parse_args()

host = "ca.wikipedia.org"
user = None
password = None
protocol = "https"
data = {}
# autpage = "User:Toniher/Autoritats"
evopagew = "Viquiprojecte:Viquidones/Evolució"

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

if "evopagew" in data:
	evopagew = data["evopagew"]

site = mwclient.Site(host, scheme=protocol)
if user and pwd:
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


def prepareListToTable(myList):
	finalList = []

	for el in myList:
		if isinstance(el, float):
			if el == 0:
				finalList.append("0")
			else:
				finalList.append("{:.4f}".format(el))
		else:
			finalList.append(str(el))

	return finalList


storehash = dict()

text = ""
extratable = ""
extrawhere = ""

extratable = ", `gender` g "
extrawhere = " and g.id=w.id"
extrasort = " order by cdate"

# Get all bios
bios = pd.read_sql_query("SELECT w.id as id, w.article as article, g.gender as gender, b.cdate as cdate, b.cuser as cuser from `bios` b, `wikidata` w "+ extratable+" where b.article=w.article "+extrawhere+extrasort, conn)

# Women = g.gender='Q6581072' We will filter down

bios_count = bios.shape[0]
storehash["bios_count"] = bios_count

bios["cdate"] = pd.to_datetime(bios["cdate"])
bios["year"] = bios["cdate"].dt.year
bios["month"] = bios["cdate"].dt.month
#bios["week"] = bios["cdate"].dt.isocalendar().week
bios["week"] = bios["cdate"].dt.week
bios["weekday"] = bios["cdate"].dt.weekday
#print(bios)

women = bios[bios.gender.eq("Q6581072")]

numarticles = bios.groupby(["year", "month"])["article"].count().reset_index()
numarticles.rename(columns={"article": "num"}, inplace=True)
numarticles["num"] = numarticles["num"].fillna(0)

numarticlesw = women.groupby(["year", "month"])["article"].count().reset_index()
numarticlesw.rename(columns={"article": "num"}, inplace=True)
numarticlesw["num"] = numarticlesw["num"].fillna(0)

merged = pd.merge(numarticles, numarticlesw, how="left", on=["year", "month"], suffixes=("", "w"))
merged["numw"] = merged["numw"].fillna(0)
merged["numw"] = merged["numw"].astype("int64")

# Cumsum here, for avoiding problem merging afterwards
merged["cumsum"] = merged["num"].cumsum()
merged["cumsumw"] = merged["numw"].cumsum()
merged["cumsumw"] = merged["cumsumw"].fillna(0)
merged["cumsumw"] = merged["cumsumw"].astype("int64")

merged["perc"] = merged["numw"] / merged["num"]
merged["perctotal"] = merged["cumsumw"] / merged["cumsum"]

#print(merged.to_records(index=False))

# Snapshot for last year in weeks
current_month = datetime.now().strftime('%m')
current_year = int(datetime.now().strftime('%Y'))
last_year = current_year - 1

span_year = str(last_year) + "-" + current_month

wnumarticles = bios.groupby(["year", "month", "week"])["article"].count().reset_index()
wnumarticles.rename(columns={"article": "num"}, inplace=True)
wnumarticles["num"] = wnumarticles["num"].fillna(0)

wnumarticlesw = women.groupby(["year", "month", "week"])["article"].count().reset_index()
wnumarticlesw.rename(columns={"article": "num"}, inplace=True)
wnumarticlesw["num"] = wnumarticlesw["num"].fillna(0)

wmerged = pd.merge(wnumarticles, wnumarticlesw, how="left", on=["year", "month", "week"], suffixes=("", "w"))

wmerged["yearmonth"] = wmerged["year"].map(str) + "-" + wmerged['month'].map(str)
wmerged["yearmonth"] = wmerged["yearmonth"].astype('datetime64[ns]')

# Copy dataframe instead
wlast = wmerged[wmerged["yearmonth"] >= span_year].copy()

wlast["num"] = wlast["num"].astype("int64")
wlast["numw"] = wlast["numw"].astype("int64")

wlast["perc"] = wlast["numw"] / wlast["num"]

wlast = wlast.drop(columns=['yearmonth'])

table = ""
wtable = ""

table = table + "\n{| class='wikitable sortable'\n"
wtable = wtable + "\n{| class='wikitable sortable'\n"

tablecolumns = ["any", "mes", "nombre", "acumulat", "nombre - dones", "acumulat - dones", "perc", "perc acumulat"]
wtablecolumns = ["any", "mes", "setmana", "nombre", "nombre - dones", "perc"]

timeperiods = []
wtimeperiods = []

numa = []
acca = []
numwa = []
accwa = []
perca = []
percwa = []
wnumwa = []

table = table + "! " + " !! ".join(tablecolumns) + "\n"
for row in merged.to_records(index=False):
	prow = row.tolist()
	table = table + "|-\n| " + " || ".join(prepareListToTable(prow))  + "\n"
	timeperiods.append(str(prow[0])+"-"+str(prow[1]))
	numwa.append(str(prow[4]))
	accwa.append(str(prow[5]))
	percwa.append(str(prow[7]))

wtable = wtable + "! " + " !! ".join(wtablecolumns) + "\n"
for row in wlast.to_records(index=False):
	prow = row.tolist()
	wtable = wtable + "|-\n| " + " || ".join(prepareListToTable(prow))  + "\n"
	wtimeperiods.append(str(prow[0])+"-"+str(prow[1])+"-"+str(prow[2]))
	wnumwa.append(str(prow[4]))

table = table + "|}\n"
wtable = wtable + "|}\n"

text = text + "\n== Biografies de dones totals ==\n"
text = text + "{{Graph:Chart|width=600|height=200|type=line|colors=purple|xAxisAngle = -40|x="+",".join(timeperiods)+"|y="+",".join(accwa)+"}}\n"

text = text + "\n== Biografies de dones per mes ==\n"
text = text + "{{Graph:Chart|width=600|height=200|type=line|colors=purple|xAxisAngle = -40|x="+",".join(timeperiods)+"|y="+",".join(numwa)+"}}\n"

text = text + "\n== Percentatge per mes ==\n"
text = text + "{{Graph:Chart|width=600|height=200|type=line|colors=purple|xAxisAngle = -40|x="+",".join(timeperiods)+"|y="+",".join(percwa)+"}}\n"

text = text + "\n== Biografies de dones per setmana el darrer any ==\n"
text = text + "{{Graph:Chart|width=600|height=200|type=line|colors=purple|xAxisAngle = -40|x="+",".join(wtimeperiods)+"|y="+",".join(wnumwa)+"}}\n"


text = text + "\n\n== Taula historial ==\n" + table
text = text + "\n\n== Taula historial per setmana el darrer any==\n" + wtable
print(text)

printToWiki(text, site, "Actualització evolució biografies", evopagew)
