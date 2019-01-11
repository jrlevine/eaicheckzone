#!/usr/bin/env python3
# test MXes
# thread version

import dns.resolver
import argparse
import sys
import pymysql
import concurrent.futures
import socket
import struct 
import smtplib

# eai dict indexed by MX addr
# contains (ndoms, name, okeai, ok8bit)

dolist = []
eai = dict()
oldtld = None
clientaddr = None
timeout = 30
replace = False
mx = dict()                             # mx'es we've already tested
dbmx = None                             # mx'es from the database
parallel = None

def process(f):
    """
    process file of the form
    domain exchange v4address
    """

    global oldtld, eai, dolist, mx, dbmx

    for l in f:
        if l.startswith('###'):  # end of tld
            if dolist:
                testmx()
            if eai:
                putaway(replace)
            eai = dict()
            print("end", oldtld)
            oldtld = None
            continue

        (dom, exch, addr) = l.split()[:3]
        #print(dom,addr)
        if dom[-1] == '.':
            dom = dom[:-1]
        if "." not in dom:
            print("mystery domain",dom)
            continue
        tld = dom.rsplit('.', maxsplit=1)[1].lower()
        if tld != oldtld:
            if dolist:
                testmx()
            if eai:
                putaway(replace)
            eai = dict()
            oldtld = tld
            print("start", oldtld)

        if addr in eai:
            eai[addr][0] += 1
            continue

        if addr in mx:
            eai[addr] = [1, exch ] + mx[addr]
            continue

        if dbmx and addr in dbmx:
            eai[addr] = [1, exch ] + dbmx[addr]
            print(addr,exch,"from db")
            continue

        # need to test this one
        eai[addr] = [ 1, exch ]
        dolist.append(addr)
        if len(dolist) >= parallel:
            testmx()

mtas = (b"Postfix", b"Sendmail", b"Exim", b"MailSite", b"protection.outlook", b"Microsoft", b"gsmtp",
    b"Haraka", b"Nemesis", b"Amazon SES", b"bizsmtp", b"MailEnable", b"MDaemon", b"CommuniGate",
    b"hostedemail", b"yahoo.com")

def tmx1(addr):
    """ test one MX in thread
    """
    #print("test", addr)
    if addr in ("0.0.0.0", "1.1.1.1", "127.0.0.1"):
        return (addr, False, False, "Noaddr")

    try:
        if clientaddr:
            sess = smtplib.SMTP(timeout=timeout, source_address=(clientaddr, 0))
        else:
            sess = smtplib.SMTP(timeout=timeout)
        if not sess:
            return (addr, False, False, "Norej")
        ms = sess.connect(addr);
        if ms[0] != 220:
            print("bad greet",ms)
            return (addr, False, False, "Nogreet")
        s = sess.ehlo()
        sess.quit()
        if s[0] != 250:
            print("bad ehlo",s)
            return (addr, False, False, "Nohelo")
        # mta signature
        print("mta sig is", ms[1])
        mta = None
        for mm in mtas:
            if mm in ms[1]:
                mta = mm
                #print("it is",mta)
                break

        #print("text is",s[1])
        r = (addr, b"SMTPUTF8" in s[1], b"8BITMIME" in s[1], mta)
        print("return",r)
        return r
    except (OSError, PermissionError, socket.timeout, TimeoutError, smtplib.SMTPServerDisconnected, ConnectionRefusedError):
        print("fail",addr)
        return (addr, False, False, "Noconn")

def testmx():
    """
    test all the MTAs in dolist
    """

    global dolist, mx

    print("test", oldtld, len(dolist))
    fl = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as tex:
        for d in dolist:
            fl.append(tex.submit(tmx1, d))

        for future in concurrent.futures.as_completed(fl):
            try:
                r = future.result()
                if r:
                    (addr,okeai,ok8bit,mtasw) = r
                    #print(addr, okeai, ok8bit,mtasw)
                    oldr = eai[addr]
                    eai[addr] = oldr[:2] + list(r[1:])
                    mx[addr] = list(r[1:])
            except Exception as exc:
                print("thread barf", exc, file=sys.stderr)
    dolist = []
        
def putaway(replace=False):
    """
    store everything in eai
    as tld oldtld
    """

    global eai,oldtld
    
    def aton(s):
        """ ipv4 to unsigned int """
        return struct.unpack(">I", socket.inet_aton(s))[0]

    db = pymysql.connect(host='g4.iecc.com',user='eaimail',password='x',db='eaimail')
    ex = [ [oldtld, aton(a)]+i for (a,i) in eai.items() if len(i) == 5]
    print("to database",ex)
    with db.cursor() as cur:
        if replace:
            cur.execute("""DELETE FROM eaimail WHERE tld=%s""", (oldtld,))

        cur.executemany("""REPLACE INTO eaimail(tld, mxip, ndomain, mx, neai,n8bit,mtasw,scandate)
            values(%s,%s,%s,%s,%s,%s,%s,DATE(NOW()))""",
            ex)
    db.commit()
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='check whether MX is EAI')
    parser.add_argument('--par', type=int, help="Do this many in parallel (default 10)");
    parser.add_argument('--timeout', type=int, help="connection timeout (default 30)");
    parser.add_argument('--addr', type=str, help="IP client address");
    parser.add_argument('--replace', action='store_true', help="replace current DB entries");
    parser.add_argument('--dbmx', action='store_true', help="use MX info from existing database");
    parser.add_argument('domains', type=str, nargs='*', help="domain exch addr aaaaddr");
    args = parser.parse_args();
    
    parallel = args.par or 10
    clientaddr = args.addr
    timeout = args.timeout or 30
    replace = args.replace
    
    if args.dbmx:
        db = pymysql.connect(host='g4.iecc.com',user='eaimail',password='x',db='eaimail')
        with db.cursor() as cur:
            r = cur.execute("""SELECT inet_ntoa(mxip),neai,n8bit,mtasw FROM eaimail GROUP BY mxip""")
            dbmx = { m[0]: [ bool(m[1]), bool(m[2]), m[3] ] for m in cur.fetchall() }
        print("fetched {} mx from db".format(len(dbmx)))

    eai = dict()
    if args.domains:
        for zf in args.domains:
            try:
                if '.gz' in zf:
                    f = gzip.open(zf, 'r')
                else:
                    f = open(zf, 'r')
            except FileNotFoundError:
                print("Cannot open file", zf)
                continue
            process(f)
            f.close()
    else:
        process(sys.stdin)

    if dolist:
        testmx()

    if eai:
        putaway(replace)
