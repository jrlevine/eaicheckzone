#!/usr/bin/env python3
# read zone files, print list of domains and MXes
# threaded version
# put summary in database

import dns.resolver
import argparse
import os
import sys
import gzip
import pymysql
import concurrent.futures

# invalid exhangers
dlocal = dns.name.Name(('localhost',''))
ddot = dns.name.Name(('',))

resolver = None
timeout = 5
maxmx = None
nmx = 0
parallel = None
tee = None

def lk1(d):
    """ lookup one domain
    return 3 or 4 tuple (domain, "mx host", 1.2.3.4 [ 1234:5678::90ab )
    use global timeout and resolver addr
    """
    r = dns.resolver.Resolver()
    r.timeout = timeout
    if resolver:
        r.nameservers = [ resolver ]

    try:
        mxlist = r.query(d,'mx')
    except (dns.exception.Timeout, dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        #print ("no mx for",d)
        return None

    #print ("found mx for",d)
    # find best mx
    minp = min((rr.preference for rr in mxlist))
    exch = tuple(rr.exchange for rr in mxlist if rr.preference == minp)[0]
    # don't return known-to-be-bogus MX
    if exch == dlocal or exch == ddot or "immediate-attention" in str(exch):
        return None
    try:
        alist = r.query(exch, 'a')
    except (dns.exception.Timeout, dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        #print ("no a for",d,exch)
        return None
    try:
        aaaalist = r.query(exch, 'aaaa')
        return (d, str(exch), str(alist[0]), str(aaaalist[0]))
    except (dns.exception.Timeout, dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        r = (d, str(exch), str(alist[0]))
        return r

def lkup(dl):
    """ do block of domains in parallel
    return number of MX
    print them out
    """
    nres = 0
    fl = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as tex:
        for d in dl:
            fl.append(tex.submit(lk1, d))

        for future in concurrent.futures.as_completed(fl):
            try:
                r = future.result()
                if r:
                    print(" ".join(r))
                    if tee:
                        print(" ".join(r), file=tee)
                    nres += 1
            except Exception as exc:
                print("thread barf", exc, file=sys.stderr)
    return nres

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get MX for 2LDs')
    parser.add_argument('--sample', type=int, help="Check every sample-th (default 100)");
    parser.add_argument('--max', type=int, help="Max number of MXes to get from each TLD");
    parser.add_argument('--par', type=int, help="Do this many in parallel");
    parser.add_argument('--res', type=str, help="Resolver to use");
    parser.add_argument('--group', type=int, help="Group size to give to parallel pool (default --par)");
    parser.add_argument('--timeout', type=int, help="DNS timeout (default 5)");
    parser.add_argument('--tee', type=str, help="copy output here");
    parser.add_argument('--v6', action='store_true', help="also check v6 address");
    parser.add_argument('zone', type=str, nargs='+', help="Zone files [.gz]");
    args = parser.parse_args();
    
    if args.sample is None:
        sample = 100
    else:
        sample = args.sample
    timeout = args.timeout or 5
    parallel = args.par
    group = args.group or parallel or 100
    resolver = args.res
    maxmx = args.max
    if args.tee:
        tee = open(args.tee, "w")

    for zf in args.zone:
        try:
            if '.gz' in zf:
                f = gzip.open(zf, 'r')
            else:
                f = open(zf, 'rb')
        except FileNotFoundError:
            print("Cannot open file", zf, file=sys.stderr)
            continue
        print("Scan {} every {}".format(zf,sample), file=sys.stderr)
        skip = sample
        zoneroot = ''
        lastdom = None
        nmx = 0
        ndom = 0
        dl = []

        for ll in f:
            l = ll.decode()
            if l[:7] == '$ORIGIN':
                zoneroot = "."+l[8:-1].lower()
                print( "Root is",zoneroot, file=sys.stderr)
                continue

            # handle NS records found in TLD zone files
            if ' NS ' in l:
                d = l[:l.index(' ')].lower()
            elif '\tin\tns\t' in l or '\tIN\tNS\t' in l:
                d = l[:l.index('\t')].lower()
            else:
                continue

            if d == lastdom or d == "" or '*' == d[0]:
                continue
            lastdom = d
            skip -= 1
            if skip > 0:
                continue
            else:
                skip = sample

            if d.endswith('.'):
                t = d
                if not zoneroot:
                    zoneroot = "."+d.split('.')[-2]+"."
                    print( "Root is",zoneroot, file=sys.stderr)
            else:    
                t = d + zoneroot

            dl.append(t)
            ndom += 1

            if len(dl) >= group:
                print("do block", zoneroot, len(dl), file=sys.stderr)
                n = lkup(dl)
                nmx += n
                print("{} found {} total {}".format(zoneroot,n,nmx), file=sys.stderr)
                dl = []
                if maxmx and nmx > maxmx:
                    break

        # do the last group
        if len(dl) > 0:
            print("do block", zoneroot, len(dl), file=sys.stderr)
            nmx += lkup(dl)

        f.close()
        print("### end",zoneroot, flush=True)
        if tee:
            print("### end",zoneroot, flush=True, file=tee)
        
        # put summary in database
        tld =  zoneroot[1:-1]
        print("Record {} ndom {} nmx {}".format(tld,ndom,nmx), file=sys.stderr)
        db = pymysql.connect(unix_socket='/tmp/mysql.sock',user='eaimail',password='x',db='eaimail')
        with db.cursor() as cur:
            nname = None                # keep nname if it's set
            if cur.execute("""SELECT nname FROM eaitld WHERE tld=%s""", (tld,)):
                nname = cur.fetchone()[0]
                print("{} has {} names".format(tld, nname), file=sys.stderr)
            cur.execute("""REPLACE INTO eaitld(tld, ndom, nmx, nname) VALUES(%s,%s,%s,%s)""",
                (tld, ndom, nmx,nname))
        db.commit()
        db.close()

    if tee:
        tee.close()
