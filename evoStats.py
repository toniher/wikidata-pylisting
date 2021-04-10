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


storehash = dict()

text = ""
extratable = ""
extrawhere = ""

extratable = ", `gender` g "
extrawhere = " and g.id=w.id and g.gender='Q6581072'"
extrasort = " order by cdate ASC limit 10000"

# Get all bios
bios = pd.read_sql_query("SELECT w.id as id, w.article as article, b.cdate as cdate, b.cuser as cuser from `bios` b, `wikidata` w "+ extratable+" where b.article=w.article "+extrawhere+extrasort, conn)

bios_count = bios.shape[0]
storehash["bios_count"] = bios_count

bios["cdate"] = pd.to_datetime(bios["cdate"])
bios["year"] = bios["cdate"].dt.year
bios["month"] = bios["cdate"].dt.month
bios["weekno"] = bios["cdate"].dt.week
bios["weekday"] = bios["cdate"].dt.weekday
print(bios)


# print(text)
#printToWiki(text, site, "Actualització de recompte d'autoritats", evopagew)