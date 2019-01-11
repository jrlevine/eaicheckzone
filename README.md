# eaicheckzone
Check for EAI mail servers on names in a DNS zone

This project has two python scripts and a mysql database.

## Overview

The first script, `checkmx.py`, reads a top-level-domain DNS zone file
looking for names delegated with NS records, and checks to see if the each name
has an MX, and writes out the ones that do, with the name and IP address of the MX.
It also stores in the database the number of domains with MXes and the number of
different MXes.

The second script, `testmx.py`, takes that list of MXes, connects to each, 
sends an EHLO command, and checks to see if the response includes the 8BITMIME
and SMTPUTF8 options.
It also looks for the names of common mail software in the intial banner.
It stores the results of its tests in the mysql database.

## Prerequisites

* dnspython

* pymysql

## checkmx.py

Zone files can be quite large, with millions of delegated names, so this script
normally samples every Nth name until it's found as many MXes as needed.  Since
the DNS lookups can be slow, it looks up many at once.

Arguments are:

`--sample N` Check every Nth name (default 100)

`--max N` Stop when it's found N MXes

`--par N` Number of domain checking threads to use (default 100)

`--group N` Check N domains ate once (default --par)

`--res n.n.n.n` DNS resolver to use (default is system default)

`--timeout N` DNS timeout in seconds (default 5)

`--tee FILE` Write a copy of the domain and MX info into FILE

`--v6` Also look for IPv6 addresses in MXes 

`zone ...` List of text or gzipped zone files

## testmx.py

Read a list of domains and MXes and check them.
It remembers the IP addresses it's checked and will only check each one once.
This speeds things up and makes the tests look less like a spambot.

Arguments:

`--par N` Test N MXes in parallel (default 10)

`--timeout N` Abandon test if no response in N seconds (default 30)

`--addr n.n.n.n` Connect from address n.n.n.n (useful on multi-homed machines)

`--replace` Replace previous results for this TLD in the database

`--dbmx` Load in previously tested MXes from the database (recommended other than on the first zone file.)

`domains ...` file(s) in format written by testmx.py, default stdin

## Examples

First create the MySQL database using the schema `eaimail.sql`.  Adjust user name and password as needed, and
be sure to change them in the two python scripts, too.

For small zones

`./checkmx.py --par 1000 --sample 1 --max 1000 --res 8.8.8.8 --tee smallmx zone1.gz zone2.gz \
 ./testmx.py --par 200 --replace --dbmx`

For larger zones

`./checkmx.py --par 1000 --sample 100 --max 10000 --tee bigmx zone1.gz zone2.gz \
 ./testmx.py --par 200 --replace --dbmx`

## Observations

It's usually faster to use a public resolver like 8.8.8.8 or 9.9.9.9 than to hammer on your local DNS cache.

To get useful results, test from a host that is not in the Spamhaus PBL or other e-mail blacklist.
(Most residential broadband networks are added to the PBL by the ISPs.)

Zone files for most ICANN contracted TLDs can be obtained by signing up at
the Centralized Zone Data Service at https://czds.icann.org/en

To get zone files for older domains including .com, .org, .info, .asia, and .biz,
you have to send an application to the domain's registry to get an FTP
password.
