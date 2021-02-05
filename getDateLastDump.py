#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests

url = "https://dumps.wikimedia.org/other/wikibase/wikidatawiki/"

page = requests.get(url).text

arrlist = []


def checkElement(checkurl, ending):
    checkpage = requests.get(checkurl).text
    soup = BeautifulSoup(checkpage, 'html.parser')
    for node in soup.find_all('a'):
        if node.get('href').endswith(ending):
            return True


soup = BeautifulSoup(page, 'html.parser')
for node in soup.find_all('a'):
    if node.get('href').endswith("/"):
        arrlist.append(node.get('href'))

arrlist.sort(reverse=True)

date = ""

for it in arrlist:
    if checkElement(url + it, "-all.json.gz"):
        date = it.replace("/", "")
        break

print(date)
