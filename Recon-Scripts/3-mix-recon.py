#!/usr/bin/env python

################################################################
## [Name]: 3-mix-recon.py -- a recon/enumeration script
## [Original Author]: Mike Czumak (T_v3rn1x) -- @SecuritySift
## [Author]: Re4son re4son [at] whitedome.com.au
##--------------------------------------------------------------
## [Details]: 
## This script is intended to be executed remotely against a 
## list of IPs to perform a detailed nmap scan.
##
## As opposed to Mike's script, this one only recommends further
## actions together with the correct command line syntax for
## cut and past actions so you get immediate high level 
## information and can focus your next steps a little better. 
################################################################

import subprocess
import multiprocessing
from multiprocessing import Process, Queue
import os
import time 

TARGETS='/root/192.168.24.0/targets.txt'
OUTDIR='/root/192.168.24.0/'			# Can be empty - will use ./mix-recon-OUTPUT
DNSSRV='192.168.24.149'				# Can be empty - will skip name resolution

def multProc(targetin, scanip, port, outputdir):
    jobs = []
    p = multiprocessing.Process(target=targetin, args=(scanip, port, outputdir))
    jobs.append(p)
    p.start()
    return

def nmapScan(ip_address, outputdir):
   ip_address = ip_address.strip()
   outfile = outputdir + "/" + ip_address + "_findings.txt"

   print "[+] Starting quick nmap scan for %s" % (ip_address)
   QUICKSCAN = "nmap -n -oN '%s/%s.quick.nmap' %s"  % (outputdir, ip_address, ip_address)
   quickresults = subprocess.check_output(QUICKSCAN, shell=True)

   print "[+] Starting detailed TCP/UDP nmap scans for %s" % (ip_address)
   serv_dict = {}
   if DNSSRV:
       TCPSCAN = "nmap -vv -Pn -sS -A -sC -p- -T 3 -script-args=unsafe=1 --dns-servers %s -oN '%s/%s.nmap' -oX '%s/%s_nmap_scan_import.xml' %s"  % (DNSSRV, outputdir, ip_address, outputdir, ip_address, ip_address)
       UDPSCAN = "nmap -vv -Pn -A -sC -sU -T 4 --top-ports 200 --dns-servers %s -oN '%s/%sU.nmap' -oX '%s/%sU_nmap_scan_import.xml' %s" % (DNSSRV, outputdir, ip_address, outputdir, ip_address, ip_address)
   else:
       TCPSCAN = "nmap -vv -Pn -sS -A -sC -p- -T 3 -script-args=unsafe=1 -n %s -oN '%s/%s.nmap' -oX '%s/%s_nmap_scan_import.xml' %s"  % (DNSSRV, outputdir, ip_address, outputdir, ip_address, ip_address)
       UDPSCAN = "nmap -vv -Pn -A -sC -sU -T 4 --top-ports 200 -n %s -oN '%s/%sU.nmap' -oX '%s/%sU_nmap_scan_import.xml' %s" % (DNSSRV, outputdir, ip_address, outputdir, ip_address, ip_address)

   results = subprocess.check_output(TCPSCAN, shell=True)
   udpresults = subprocess.check_output(UDPSCAN, shell=True)
   lines = results.split("\n")
   for line in lines:
      ports = []
      line = line.strip()
      if ("tcp" in line) and ("open" in line) and not ("Discovered" in line):
	 while "  " in line: 
            line = line.replace("  ", " ");
         service = line.split(" ")[2] # grab the service name
	 port = line.split(" ")[0] # grab the port/proto
         if service in serv_dict:
	    ports = serv_dict[service] # if the service is already in the dict, grab the port list
	 
         ports.append(port) 
	 serv_dict[service] = ports # add service to the dictionary along with the associated port(2)
   
   # go through the service dictionary to give some hints for further enumerations 
   f = open(outfile, 'w')
   for serv in serv_dict: 
      ports = serv_dict[serv]
      if ("ftp" in serv):
 	 for port in ports:
	    port = port.split("/")[0]
	    f.write("[*] Found FTP service on %s:%s\n" % (scanip, port))
	    f.write("   [>] Use nmap scripts for further enumeration or hydra for password attack, e.g\n")
	    f.write("   [=] nmap -sV -Pn -vv -p%s --script=ftp-anon,ftp-bounce,ftp-libopie,ftp-proftpd-backdoor,ftp-vsftpd-backdoor,ftp-vuln-cve2010-4221 -oN '%s/%s_ftp.nmap' -oX '%s/%s_ftp_nmap_scan_import.xml' %s\n" % (port, outputdir, scanip, outputdir, scanip, scanip))
	    f.write("   [=] hydra -L /usr/share/wordlists/webslayer/others/names.txt -P /usr/share/wordlists/webslayer/others/common_pass.txt -f -o %s/%s_ftphydra.txt -u %s -s %s ftp\n" % (outputdir, scanip, scanip, port))	
      elif (serv == "http"):
 	 for port in ports:
	    port = port.split("/")[0]
	    f.write("[*] Found HTTP service on %s:%s\n" % (scanip, port))
	    f.write("   [>] Use nikto & dirb / dirbuster for service enumeration, e.g\n")
	    f.write("   [=] nikto -h %s -p %s > %s/%s_nikto.txt\n" % (scanip, port, outputdir, scanip))
	    f.write("   [=] dirb http://%s:%s/ -o %s/%s_dirb.txt -r -S -x ./dirb-extensions/php.ext\n" % (scanip, port, outputdir, scanip))
	    f.write("   [=] java -jar /usr/share/dirbuster/DirBuster-1.0-RC1.jar -H -l /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt -r %s/%s_dirbuster.txt -u http://%s:%s/\n" % (outputdir, scanip, scanip, port))
      elif (serv == "ssl/http") or ("https" in serv):
	 for port in ports:
	    port = port.split("/")[0]
	    f.write("[*] Found HTTP service on %s:%s\n" % (scanip, port))
	    f.write("   [>] Use nikto & dirb / dirbuster for service enumeration, e.g\n")
	    f.write("   [=] nikto -h %s -p %s > %s/%s_nikto.txt\n" % (scanip, port, outputdir, scanip))
	    f.write("   [=] dirb https://%s:%s/ -o %s/%s_dirb.txt -r -S -x ./dirb-extensions/php.ext\n" % (scanip, port, outputdir, scanip))
	    f.write("   [=] java -jar /usr/share/dirbuster/DirBuster-1.0-RC1.jar -H -l /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt -r %s/%s_dirbuster.txt -u http://%s:%s/\n" % (outputdir, scanip, scanip, port))
      elif "mysql" in serv:
 	 for port in ports:
	    port = port.split("/")[0]
	    f.write("[*] Found mysql service on %s:%s\n" % (scanip, port))
	    f.write("   [>] Check out the server for web applications with sqli vulnerabilities\n")
      elif "microsoft-ds" in serv:	
 	 for port in ports:
	    port = port.split("/")[0]
	    f.write("[*] Found MS SMB service on %s:%s\n" % (scanip, port))
	    f.write("   [>] Use nmap scripts or enum4linux for further enumeration, e.g\n")
	    f.write("   [=] nmap -sV -Pn -vv -p%s --script=\"smb-* -oN '%s/%s_smb.nmap' -oX '%s/%s_smb_nmap_scan_import.xml' %s\n" % (port, outputdir, ip_address, outputdir, ip_address, ip_address))
	    f.write("   [=] enum4linux %s\n" % (scanip))
      elif "ms-sql" in serv:
 	 for port in ports:
	    port = port.split("/")[0]
	    f.write("[*] Found MS SQL service on %s:%s\n" % (scanip, port))
	    f.write("   [>] Use nmap scripts for further enumeration, e.g\n")
	    f.write("   [=] nmap -vv -sV -Pn -p %s --script=ms-sql-info,ms-sql-config,ms-sql-dump-hashes --script-args=mssql.instance-port=%s,smsql.username-sa,mssql.password-sa -oX %s/%s_mssql_nmap_scan_import.xml %s" % (port, port, outputdir, ip_address, ip_address))
      elif ("msdrdp" in serv) or ("ms-wbt-server" in serv):
 	 for port in ports:
	    port = port.split("/")[0]
	    f.write("[*] Found RDP service on %s:%s\n" % (scanip, port))
	    f.write("   [>] Use ncrackpassword cracking, e.g\n")
	    f.write("   [=] ncrack -vv --user administrator -P /root/rockyou.txt rdp://%s\n" % (scanip))
      elif "smtp" in serv:
 	 for port in ports:
	    port = port.split("/")[0]
	    f.write("[*] Found SMTP service on %s:%s\n" % (scanip, port))
	    f.write("   [>] Use smtp-user-enum to find users, e.g\n")
	    f.write("   [=] smtp-user-enum -M VRFY -U /usr/share/wfuzz/wordlist/fuzzdb/wordlists-user-passwd/names/namelist.txt -t %s -p %s\n" % (scanip, port))
      elif "snmp" in serv:
 	 for port in ports:
	    port = port.split("/")[0]
	    f.write("[*] Found SNMP service on %s:%s\n" % (scanip, port))
	    f.write("   [>] Use nmap scripts, onesixtyone or snmwalk for further enumeration, e.g\n")
	    f.write("   [=] nmap -sV -Pn -vv -p%s --script=snmp-netstat,snmp-processes -oN '%s/%s_snmp.nmap' -oX '%s/%s_snmp_nmap_scan_import.xml' %s\n" % (port, outputdir, scanip, outputdir, scanip, scanip))
	    f.write("   [=] onesixtyone %s\n" % (scanip))
	    f.write("   [=] snmpwalk -c public -v1 %s > %s/%s_snmpwalk.txt\n" % (scanip, outputdir, scanip))
      elif "ssh" in serv:
 	 for port in ports:
	    port = port.split("/")[0]
	    f.write("[*] Found SSH service on %s:%s\n" % (scanip, port))
	    f.write("   [>] Use medusa or hydra (unreliable) for password cracking, e.g\n")
	    f.write("   [=] medusa -u root -P /root/rockyou.txt -e ns -h %s - %s -M ssh\n" % (scanip, port))
	    f.write("   [=] hydra -f -V -t 1 -l root -P /root/rockyou.txt -s %s %s ssh\n" % (port, scanip))
   f.close()     
   print "[*] TCP/UDP Nmap scans completed for " + ip_address 
   return

# grab the ping sweep results and start scanning up hosts
print "\n"
print "############################################################"
print "####               NETWORK RECONNAISSANCE               ####"
print "############################################################"
print "\n"
 
if __name__=='__main__':
   f = open(TARGETS, 'r')

   if OUTDIR == '':
       OUTDIR = "./mix-recon-OUTPUT"

   try:
       os.stat(OUTDIR)
   except:
       os.mkdir(OUTDIR)

   for scanip in f:
       scanip = scanip.strip()
       print "[+] Creating directory structure for " + scanip

       hostdir = OUTDIR + "/" + scanip
       try:
           os.stat(hostdir)
       except:
           os.mkdir(hostdir)

       nmapdir = hostdir + "/nmap"
       try:
           os.stat(nmapdir)
       except:
           os.mkdir(nmapdir)

       exploitdir = hostdir + "/exploit"
       try:
           os.stat(exploitdir)
       except:
           os.mkdir(exploitdir)

       lootdir = hostdir + "/loot"
       try:
           os.stat(lootdir)
       except:
           os.mkdir(lootdir)

       prooffile = hostdir + "/proof.txt"
       open(prooffile, 'a').close()

       namefile = hostdir + "/0-name"
       open(namefile, 'a').close()

       jobs = []
       p = multiprocessing.Process(target=nmapScan, args=(scanip, nmapdir))
       jobs.append(p)
       p.start()
   f.close() 
