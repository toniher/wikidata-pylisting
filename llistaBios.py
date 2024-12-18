#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import io
import json
import pprint
import time
from urllib import request
from urllib.parse import unquote

import mwclient
import MySQLdb
import pandas as pd
import requests

pp = pprint.PrettyPrinter(indent=4)

# Import JSON configuration
parser = argparse.ArgumentParser(description="""Script for testing MediaWiki API""")
parser.add_argument(
    "--config", help="""Path to a JSON file with configuration options!"""
)
parser.add_argument("--lang", help="""Wiki language to use""")
parser.add_argument("--reuse", action="store_true", help="Reuse")

args = parser.parse_args()

# Default wiki language
wikilang = "ca"

host = "ca.wikipedia.org"
user = None
pwd = None
protocol = "https"

if "lang" in args:
    if args.lang is not None:
        wikilang = args.lang
        host = wikilang + ".wikipedia.org"

data = {}
targetpage = "User:Toniher/Bios"
milestonepage = "Plantilla:NumBios"
targetpagedones = "Viquiprojecte:Viquidones/Progrés"
milestonepagedones = "Plantilla:FitaDones"

checkpage = "User:Toniher/CheckBios"
checkgender = "User:Toniher/CheckGender"
checkdisgender = "User:Toniher/CheckDisGender"
checkmultigender = "User:Toniher/CheckMultiGender"

countgenderpage = "User:Toniher/StatsGender"

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
    conn = MySQLdb.connect(
        host=data["mysql"]["host"],
        user=data["mysql"]["user"],
        passwd=data["mysql"]["password"],
        db=data["mysql"]["database"],
        use_unicode=True,
        charset="utf8mb4",
        init_command="SET NAMES utf8mb4",
    )

if "targetpage" in data:
    targetpage = data["targetpage"]

if "milestonepage" in data:
    milestonepage = data["milestonepage"]

if "checkpage" in data:
    checkpage = data["checkpage"]

site = mwclient.Site(host, scheme=protocol)
if user and pwd:
    # Login parameters
    site.login(user, pwd)

if conn is None:
    print("CONNECTION PROBLEM")
    exit()

cur = conn.cursor()


def checkWikiDataJSON(item, type="iw", lang="ca"):
    output = []

    # If item exists and starts with Q
    if item and (item.startswith("Q") or item.startswith("P")):
        url = "https://www.wikidata.org/wiki/Special:EntityData/" + item + ".json"

        if type != "iw":
            print(url)

        req = request.Request(url)

        # parsing response
        r = request.urlopen(req).read()
        cont = json.loads(r.decode("utf-8"))

        # parsing json
        entitycont = cont["entities"][item]

        if type == "label":
            if "labels" in entitycont:
                if lang in entitycont["labels"]:
                    output.append(entitycont["labels"][lang]["value"])
        else:
            if "sitelinks" in entitycont:
                output = list(entitycont["sitelinks"])

        time.sleep(0.5)
    return output


def insertInDB(new_stored, lang, conn):
    c = conn.cursor()

    for index, row in new_stored.iterrows():
        # Handling Timezone
        row["cdate"] = row["cdate"].replace("T", " ")
        row["cdate"] = row["cdate"].replace("Z", "")

        # Check problem user
        if (
            row["cuser"] == ""
            or row["cuser"] == "nan"
            or not row["cuser"]
            or isinstance(row["cuser"], float)
        ):
            print("NO USER AT: " + row["article"])
            row["cuser"] = None

        c.execute(
            "SELECT * from bios where BINARY article = %s and lang = %s",
            [row["article"], lang],
        )
        if c.rowcount > 0:
            print("UPDATE " + row["article"])
            c.execute(
                "UPDATE `bios` SET `cdate` = %s, `cuser` = %s where BINARY article = %s and lang = %s",
                [row["cdate"], row["cuser"], row["article"], lang],
            )
        else:
            print("INSERT " + row["article"])
            c.execute(
                "INSERT INTO `bios` (`article`, `lang`, `cdate`, `cuser`) VALUES (%s, %s, %s, %s)",
                [row["article"], lang, row["cdate"], row["cuser"]],
            )

    conn.commit()

    return True


def printToWiki(toprint, mwclient, targetpage, milestonepage):
    count = toprint.shape[0]
    i = 0

    print(count)
    columns = toprint.columns.values.tolist()
    columns.remove("lang")
    text = (
        "{| class='wikitable sortable' \n!" + "ordre !! " + " !! ".join(columns) + "\n"
    )

    for index, row in toprint.head(100).iterrows():
        num = count - i
        text = (
            text
            + "|-\n|"
            + str(num)
            + " || "
            + "[[d:"
            + row["item"]
            + "|"
            + row["item"]
            + "]]"
            + " || "
            + row["genere"]
            + " || "
            + " [["
            + row["article"]
            + "]]"
            + " || "
            + str(row["cdate"])
            + " || "
            + "{{u|"
            + str(row["cuser"])
            + "}}"
            + "\n"
        )
        i = i + 1

    text = text + "|}"

    page = site.pages[targetpage]
    page.save(text, summary="Bios", minor=False, bot=True)

    if milestonepage:
        sittext = str(count) + "\n<noinclude>[[Categoria:Plantilles]]</noinclude>"
        page = site.pages[milestonepage]
        page.save(sittext, summary="Bios", minor=False, bot=True)

    return True


def saveToDb(toprint, conn):
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS `wikidata`;")
    c.execute(
        "CREATE TABLE IF NOT EXISTS `wikidata` ( `id` varchar(24), `article` VARCHAR(255) ) default charset='utf8mb4' collate='utf8mb4_bin';"
    )
    c.execute("CREATE INDEX IF NOT EXISTS `idx_unique` ON wikidata (id, article);")
    c.execute("CREATE INDEX IF NOT EXISTS `idx_id` ON wikidata (id);")
    c.execute("CREATE INDEX IF NOT EXISTS `idx_article` ON wikidata (article);")
    c.execute("DROP TABLE IF EXISTS `gender`;")
    c.execute(
        "CREATE TABLE IF NOT EXISTS `gender` ( `id` varchar(24), `gender` VARCHAR(24) ) default charset='utf8mb4' collate='utf8mb4_bin';"
    )
    c.execute("CREATE INDEX IF NOT EXISTS `idx_unique` ON gender (id, gender);")
    c.execute("CREATE INDEX IF NOT EXISTS `idx_id` ON gender (id);")
    c.execute("CREATE INDEX IF NOT EXISTS `idx_gender` ON gender (gender);")

    c.execute(
        "CREATE TABLE IF NOT EXISTS `run` (  `date` datetime DEFAULT CURRENT_TIMESTAMP, `name` VARCHAR(25), PRIMARY KEY (`date`, `name`) ) ;"
    )
    c.execute("INSERT INTO `run` (`name`) VALUES (%s)", ["bios"])

    for index, row in toprint.iterrows():
        if row["genere"] == "nan":
            row["genere"] = None

        c.execute(
            "INSERT INTO `gender` (`id`, `gender`) VALUES (%s, %s)",
            [row["item"], row["genere"]],
        )

    conn.commit()

    toprint = toprint.drop_duplicates(subset=["item", "article"], keep="last")
    for index, row in toprint.iterrows():
        c.execute(
            "INSERT INTO `wikidata` (`id`, `article`) VALUES (%s, %s)",
            [row["item"], row["article"]],
        )

    conn.commit()

    return True


def cleanDb(conn):
    c = conn.cursor()
    c.execute("SELECT * from wikidata")

    if c.rowcount > 0:
        # TODO Proceed cleaning
        c.execute(
            "delete from bios where article in (select b.article from bios b left join wikidata w on b.article=w.article where w.id is null order by b.article ) ;"
        )

    conn.commit()

    return True


def printCheckWiki(
    toprint, mwclient, checkpage, checkwd=True, checkgen=True, lang="ca"
):
    if checkgen:
        header = ["wikidata", "genere", "article"]
    else:
        header = ["wikidata", "article"]

    if checkwd:
        text = (
            "{| class='wikitable sortable' \n!"
            + " !! ".join(header)
            + "!! iwiki !! iwikicount\n"
        )
    else:
        text = "{| class='wikitable sortable' \n!" + " !! ".join(header) + "\n"

    for index, row in toprint.iterrows():
        genstr = ""
        if checkgen:
            genstr = " || " + str(row["genere"])

        if checkwd is True:
            iwiki = checkWikiDataJSON(str(row["item"]), "iw", lang)
            iwikicount = len(iwiki)
            text = (
                text
                + "|-\n|"
                + "[[d:"
                + str(row["item"])
                + "|"
                + str(row["item"])
                + "]]"
                + genstr
                + " || "
                + " [["
                + str(row["article"])
                + "]]"
                + " || "
                + ", ".join(iwiki)
                + "|| "
                + str(iwikicount)
                + "\n"
            )
        else:
            text = (
                text
                + "|-\n|"
                + "[[d:"
                + str(row["item"])
                + "|"
                + str(row["item"])
                + "]]"
                + genstr
                + " || "
                + " [["
                + str(row["article"])
                + "]]"
                + "\n"
            )

    text = text + "|}"

    page = site.pages[checkpage]
    page.save(text, summary="Bios", minor=False, bot=True)

    return True


def printCountGenere(toprint, mwclient, checkpage, bios_count, wikilang="ca"):
    list_generes = []
    text = (
        "{| class='wikitable sortable' \n!"
        + " !! ".join(["gènere", "recompte", "percentatge"])
        + "\n"
    )

    for index, row in toprint.iterrows():
        genere = "NA"

        if row["genere"] == "unknown":
            genere = "desconegut"
        elif row["genere"] == "nan":
            genere = "no assignat"
        else:
            genereA = checkWikiDataJSON(str(row["genere"]), "label", wikilang)
            if len(genereA) > 0:
                genere = genereA[0]
            else:
                genere = row["genere"]

        list_generes.append(genere)
        perc = (row["count"] / bios_count) * 100
        percstr = "%2.3f" % perc
        text = (
            text
            + "|-\n| [["
            + str(genere)
            + "]] || "
            + str(row["count"])
            + "||"
            + str(percstr)
            + "\n"
        )

    text = text + "|}"

    text = text + "\n----\n"

    text = (
        text
        + "* {{#expr: {{NumBios}} + 0 }} biografies - [["
        + targetpage
        + "|Seguiment]]\n"
    )
    text = (
        text
        + "* {{#expr: {{FitaDones}} + 0 }} biografies de dones - [["
        + targetpagedones
        + "|Seguiment]]\n"
    )
    text = (
        text
        + "* COMPROVACIONS: [["
        + checkgender
        + "|Sense gènere]] - [["
        + checkmultigender
        + "|Múltiples gèneres]] - [["
        + checkdisgender
        + "|Desconegut]] \n"
    )

    text = (
        text
        + "''NOTA: Algunes biografies poden tenir correctament assignades més d'un genère.''\n"
    )
    text = text + "\n----\n"

    list_count = map(lambda x: str(x), toprint["count"].tolist())
    text = (
        text
        + "{{Graph:Chart|width=100|height=100|type=pie|legend=Llegenda|x="
        + ",".join(list_generes)
        + "|y="
        + ",".join(list_count)
        + "|showValues=}}"
    )

    page = site.pages[checkpage]
    page.save(text, summary="Recompte gènere", minor=False, bot=True)

    return True


cur.execute(
    "CREATE TABLE IF NOT EXISTS `bios` ( `article` VARCHAR(255), `lang` VARCHAR(10), `cdate` datetime, `cuser` VARCHAR(255) ) default charset='utf8mb4' collate='utf8mb4_bin';"
)
cur.execute("CREATE INDEX IF NOT EXISTS `idx_article` ON bios (`article`);")
cur.execute("CREATE INDEX IF NOT EXISTS `idx_lang` ON bios (`lang`);")
cur.execute("CREATE INDEX IF NOT EXISTS `idx_cdate` ON bios (`cdate`);")
cur.execute("CREATE INDEX IF NOT EXISTS `idx_cuser` ON bios (`cuser`);")

query = """
SELECT ?item ?genere ?article WHERE {{
    ?item wdt:P31 wd:Q5 .
    ?article schema:about ?item .
    ?article schema:isPartOf <https://{host}/> .
    #SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],{lang}" }} .
    OPTIONAL {{
        ?item wdt:P21 ?genere .
    }}
}} ORDER BY ?article
""".format(host=host, lang=wikilang)

headers = {
    "Accept": "text/csv",
    "User-Agent": "darreresBio/0.1.0 (https://github.com/WikimediaCAT/wikidata-pylisting; toniher@wikimedia.cat) Python/3.7",
}
params = {"query": query}
response = requests.get(
    "https://query.wikidata.org/sparql", headers=headers, params=params
)

c = pd.read_csv(io.StringIO(response.content.decode("utf-8")))

c["article"] = c["article"].apply(
    lambda x: unquote(x.replace("https://ca.wikipedia.org/wiki/", ""))
)
c["genere"] = c["genere"].astype("str")
c["genere"] = c["genere"].apply(
    lambda x: x.replace("http://www.wikidata.org/entity/", "")
)

c["genere"] = c["genere"].apply(lambda x: "unknown" if x.startswith("_") else x)

c["genere"] = c["genere"].apply(lambda x: "unknown" if "wikidata.org" in x else x)

c["item"] = c["item"].apply(lambda x: x.replace("http://www.wikidata.org/entity/", ""))

# Double check outcome
c.to_csv("/tmp/allbios.csv", index=False)

# Get stored info
stored = pd.read_sql_query("SELECT * from `bios`", conn)

# Merge both subsets centered in actual data
current = pd.merge(c, stored, how="left", on="article")

# Iterate only entries with null user or timestamp
missing = current[(current["cuser"].isnull()) & (current["cdate"].isnull())]
print("MISSING CUSER OR CDATE")
print(missing)


def retrieve_creation(missing):
    new_stored = pd.DataFrame(columns=["article", "cdate", "cuser"])

    # Define the number of retries and the delay between retries
    max_retries = 3
    retry_delay = 30  # seconds

    for index, row in missing.iterrows():
        titles = row["article"]
        print(titles)
        retries = 0
        result = None
        while retries < max_retries:
            try:
                result = site.api(
                    "query",
                    prop="revisions",
                    rvprop="timestamp|user",
                    rvdir="newer",
                    rvlimit=1,
                    titles=titles,
                )
                break  # Exit the loop if the API call is successful
            except Exception as e:
                print(f"API call failed: {e}")
                retries += 1
                if retries < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max retries reached. Skipping this article.")
                    result = None
                    break
        if result:
            for page in result["query"]["pages"].values():
                if "revisions" in page:
                    if len(page["revisions"]) > 0:
                        timestamp = None
                        userrev = None

                        if "timestamp" in page["revisions"][0]:
                            timestamp = page["revisions"][0]["timestamp"]
                        if "user" in page["revisions"][0]:
                            userrev = page["revisions"][0]["user"]

                        new_stored = new_stored.append(
                            {"article": titles, "cdate": timestamp, "cuser": userrev},
                            ignore_index=True,
                        )
                        time.sleep(1)

    return new_stored


if not args.reuse:
    new_stored = retrieve_creation(missing)

    print("MISSING WITH EXTRA INFO FROM API")
    print(new_stored)

    # We store here just in case
    new_stored.to_csv("/tmp/allbios.missing.csv", index=False)
else:
    new_stored = pd.read_csv("/tmp/allbios.missing.csv")

# INSERT or REPLACE sqlite new_stored
insertInDB(new_stored, wikilang, conn)

# Repeat stored
stored2 = pd.read_sql_query("SELECT * from `bios`", conn)

# Merge both subsets centered in actual data
current2 = pd.merge(c, stored2, how="left", on="article")

# Here we list, order and have fun
toprint = current2.sort_values(by="cdate", ascending=False)
toprint = toprint[(toprint["cdate"].notnull())]

# Clean duplicates, keeping gender
clean_duplicates = toprint.drop_duplicates(
    subset=["item", "article", "genere"], keep="last"
)

# Clean diplicates, removing several genders
clean_duplicates_full = toprint.drop_duplicates(subset=["item", "article"], keep="last")

bios_count = clean_duplicates_full.shape[0]

printToWiki(clean_duplicates_full, mwclient, targetpage, milestonepage)

dones = toprint[toprint["genere"] == "Q6581072"]
printToWiki(dones, mwclient, targetpagedones, milestonepagedones)

# We store everything in DB

# Clean a bit
saveToDb(clean_duplicates, conn)
cleanDb(conn)

# Moved pages
printCheckWiki(current2[(current2["cdate"].isnull())], mwclient, checkpage, True)

# Print missing gender
printCheckWiki(
    clean_duplicates[clean_duplicates["genere"] == "nan"].sort_values(
        by="article", ascending=True
    ),
    mwclient,
    checkgender,
    False,
    False,
)

# Print gender marked as unknown
printCheckWiki(
    clean_duplicates[clean_duplicates["genere"] == "unknown"].sort_values(
        by="article", ascending=True
    ),
    mwclient,
    checkdisgender,
    False,
    False,
)

# Print Gender Counts
countgenere = (
    clean_duplicates[["item", "genere"]]
    .groupby("genere")["item"]
    .count()
    .reset_index(name="count")
    .sort_values(["count"], ascending=False)
)
print(countgenere)

printCountGenere(countgenere, mwclient, countgenderpage, bios_count, wikilang)

groupgender = (
    clean_duplicates.groupby(["item", "article"]).size().reset_index(name="count")
)
printCheckWiki(
    groupgender[groupgender["count"] > 1].sort_values(by="article", ascending=True),
    mwclient,
    checkmultigender,
    False,
    False,
)

conn.close()
