#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import pprint
import MySQLdb
import re
import json
import csv
import gzip  # Using gzip file

pp = pprint.PrettyPrinter(indent=4)

parser = argparse.ArgumentParser(description="""Script for parsing authorities from dumps and DB""")
parser.add_argument("-dump",help="""Path to Dump file""")
parser.add_argument("-authorities",help="""Path to Authorities file""")
parser.add_argument("-config",help="""Path to a JSON file with configuration options!""")
args = parser.parse_args()

data = {}
authorities = {}
authtypes = {}
mysqlmode = False

conn = None

if "config" in args:
    if args.config is not None:
        with open(args.config) as json_data_file:
            data = json.load(json_data_file)

if "mysql" in data:
    dbfile = None
    mysqlmode = True
    conn = MySQLdb.connect(host=data["mysql"]["host"], user=data["mysql"]["user"], passwd=data["mysql"]["password"], db=data["mysql"]["database"], use_unicode=True, charset='utf8', init_command='SET NAMES UTF8')


if conn is None:
    print("NO CONNECTION")
    exit()


def addToDb( id, props, conn, iter ):

    c = conn.cursor()
    records = []

    for prop in props:
        records.append( ( id, prop ) )

    c.executemany( "INSERT INTO `authorities` (`id`, `authority`) VALUES ( %s, %s )", records )

    if iter > 10000 :
        conn.commit()
        iter = 0
    else :
        iter = iter + 1

    return iter


if "authorities" in args:
    if args.authorities is not None:
        with open(args.authorities) as authorities_file:
            csvreader = csv.reader(authorities_file, delimiter='\t')
            for row in csvreader:
                authorities[row[2]] = 1
                authtypes[row[2]] = [ row[0], row[1], row[2], row[3] ]

#pp.pprint( authorities )

if "dump" in args:
    if args.dump is not None:

        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS `run` (  `date` datetime DEFAULT CURRENT_TIMESTAMP, `name` VARCHAR(25), PRIMARY KEY (`date`, `name`) ) ;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_date ON run (date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_name ON run (name);")

        cur.execute("DROP TABLE IF EXISTS `authorities`;")
        cur.execute("CREATE TABLE IF NOT EXISTS `authorities` (  `id` VARCHAR(25), `authority` VARCHAR(25), PRIMARY KEY (`id`, `authority`) ) ;")
        cur.execute("CREATE INDEX idx_id ON authorities (id);")
        cur.execute("CREATE INDEX idx_authorities ON authorities (authority);")

        cur.execute("DROP TABLE IF EXISTS `authtypes`;")
        cur.execute("CREATE TABLE IF NOT EXISTS `authtypes` (  `name` VARCHAR(25), `desc` VARCHAR(125), `prop` VARCHAR(25), `authtype` int(2), PRIMARY KEY (`prop`) ) ;")
        cur.execute("CREATE INDEX IF NOT EXISTS `idx_name` ON authtypes (name);")
        cur.execute("CREATE INDEX IF NOT EXISTS `idx_type` ON authtypes (authtype);")

        cur.execute("INSERT INTO `run` (`name`) VALUES (%s)", ["auth"])

        # Fill authtypes
        for prop in authtypes:
            cur.execute( "INSERT INTO `authtypes` (`name`, `desc`, `prop`, `authtype`) VALUES ( %s, %s, %s, %s )", [ authtypes[prop][0], authtypes[prop][1], authtypes[prop][2], authtypes[prop][3] ] )

        iter = 0
        id = None
        with gzip.open(args.dump,'rt') as f:
            for line in f:
                detectid = re.findall( r'\"type\":\"item\",\"id\":\"(Q\d+)\"', line )
                if len( detectid ) > 0:
                    id = detectid[0]
                    # print( id )
                    listp = re.findall( r'\"(P\d+)\"', line )
                    authp = []
                    for prop in listp:
                        if prop in authorities:
                            authp.append( prop )
                    # pp.pprint( authp )
                    if len( authp ) > 0 and id is not None :
                        iter = addToDb( id, list(set(authp)), conn, iter )
                        id = None

        conn.commit()
