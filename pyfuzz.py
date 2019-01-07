#!/usr/bin/env python3
####
### Project: Pyfuzz
### Version: 1.0.0
### Creator: Ayoob Ali ( www.AyoobAli.com )
### License: MIT
###
import http.client
import sys
import os
import getopt
from optparse import OptionParser
import string
import signal
import ssl
from time import sleep
import random

logFile = ""

def signal_handler(signal, frame):
	print("\nScan stopped by user.")
	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def printMSG(printM):
    print(printM)
    if logFile != "":
        fhandle = open(logFile, "a")
        fhandle.write(printM + "\n")
        fhandle.close()

def main():
    global logFile
    parser = OptionParser(usage="%prog -u http://example.com/en/ -l sharepoint.txt", version="%prog 1.0.0")
    parser.add_option("-u", "--url", dest="targetURL", metavar="URL", help="Target URL to scan")
    parser.add_option("-l", "--list", dest="listFile", metavar="FILE", help="List of paths to scan")
    parser.add_option("-r", "--redirect", action="store_true", dest="showRedirect", help="Show redirect codes (3xx)")
    parser.add_option("-e", "--error", action="store_true", dest="showError", help="Show Error codes (5xx)")
    parser.add_option("-s", "--sleep", dest="milliseconds", type="int", metavar="NUMBER", help="Sleep for x milliseconds after each request")
    parser.add_option("-a", "--header", action="append", dest="headers", help="Add Header to the HTTP request (Ex.: -a User-Agent x)", metavar='HEADER VALUE', nargs=2)
    parser.add_option("-b", "--body", dest="requestBody", metavar="Body", help="Request Body (Ex.: name=val&name2=val2)")
    parser.add_option("-x", "--method", dest="requestMethod", metavar="[Method]", help="HTTP Request Method")
    parser.add_option("-i", "--ignore", action="append", dest="ignoreText", metavar="Text", help="Ignore results that contain a specific string")
    parser.add_option("-m", "--min-response-size", dest="dataLength", type="int", metavar="NUMBER", help="The minimum response body size in Byte")
    parser.add_option("-g", "--log", dest="logFile", metavar="FILE", help="Log scan results to a file")
    parser.add_option("-f", "--start-from", dest="startFrom", type="int", metavar="NUMBER", help="Start scanning from URL number x in the provided list")
    parser.add_option("-t", "--timeout", dest="reqTimeout", type="int", metavar="Seconds", help="Set request timeout.")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="Show error messages")

    startFrom = 0
    reqTimeout = 15

    (options, args) = parser.parse_args()

    if options.requestMethod == None:
        options.requestMethod = "GET"

    if options.requestBody == None:
        options.requestBody = ""

    if options.dataLength == None:
        options.dataLength = 0

    requestHeaders = {}
    if options.headers == None:
        options.headers = []

    for header in options.headers:
        requestHeaders.update({header[0]: header[1]})

    if options.listFile == None or options.targetURL == None:
        parser.print_help()
        sys.exit()

    if options.logFile != None:
        logFile = options.logFile

    if options.startFrom != None:
        startFrom = options.startFrom

    if options.reqTimeout != None:
        if options.reqTimeout > 0:
            reqTimeout = int(options.reqTimeout)

    if not os.path.isfile(options.listFile):
        printMSG("Error: File (" + options.listFile + ") doesn't exist.")
        sys.exit()

    if options.targetURL[-1] != "/":
        options.targetURL += "/"

    targetPro = ""

    if options.targetURL[:5].lower() == 'https':
        targetDomain = options.targetURL[8:].split("/",1)[0].lower()
        targetPath = "/" + options.targetURL[8:].split("/",1)[1]
        connection = http.client.HTTPSConnection(targetDomain, timeout=reqTimeout, context=ssl._create_unverified_context())
        targetPro = "https://"
        printMSG("Target       : " + targetPro+targetDomain + " (over HTTPS)")
        printMSG("Path         : " + targetPath)
    elif options.targetURL[:5].lower() == 'http:':
        targetDomain = options.targetURL[7:].split("/",1)[0].lower()
        targetPath = "/"+options.targetURL[7:].split("/",1)[1]
        connection = http.client.HTTPConnection(targetDomain)
        targetPro = "http://"
        printMSG("Target       : " + targetDomain)
        printMSG("Path         : " + targetPath)
    else:
        targetDomain = options.targetURL.split("/",1)[0].lower()
        targetPath = "/"+options.targetURL.split("/",1)[1]
        connection = http.client.HTTPConnection(targetDomain)
        targetPro = "http://"
        printMSG("Target       : " + targetDomain)
        printMSG("Path         : " + targetPath)

    printMSG("Method       : " + options.requestMethod)
    printMSG("Header       : " + str(requestHeaders))
    printMSG("Body         : " + options.requestBody)
    printMSG("Timeout      : " + str(reqTimeout))

    if options.showRedirect != None:
        printMSG("Show Redirect:  ON")
    if options.showError != None:
        printMSG("Show Error   :  ON")

    try:
        randomPage = ''.join([random.choice(string.ascii_lowercase + string.digits) for n in range(16)])
        connection.request(options.requestMethod, targetPath+randomPage+".txt", options.requestBody, requestHeaders)
        res = connection.getresponse()
    except Exception as ErrMs:
        if options.verbose != None:
            printMSG("MainError: " + str(ErrMs))
        sys.exit(0)

    if res.status == 200:
        printMSG("NOTE: Looks like the server is returning code 200 for all requests, there might be lots of false positive links.")

    if res.status >= 300 and res.status < 400 and options.showRedirect != None:
        printMSG("NOTE: Looks like the server is returning code " + res.status + " for all requests, there might be lots of false positive links. try to scan without the option -r")

    tpData = res.read()

    with open(options.listFile) as lFile:
        pathList = lFile.readlines()
    totalURLs = len(pathList)
    printMSG ("Scanning ( " + str(totalURLs) + " ) files...")
    countFound = 0
    countAll = 0
    strLine = ""
    for pathLine in pathList:
        try:
            countAll = countAll + 1
            pathLine = pathLine.strip("\n")
            pathLine = pathLine.strip("\r")
            if countAll < startFrom:
                continue
            if pathLine != "":
                if options.milliseconds != None:
                    sleep(options.milliseconds/1000)
                if pathLine[:1] == "/":
                    pathLine = pathLine[1:]
                print (' ' * len(strLine), "\r", end="")
                strLine = "Checking ["+str(countAll)+"/"+str(totalURLs)+"] "+targetPath+pathLine
                print (strLine,"\r", end="")
                connection.request(options.requestMethod, targetPath+pathLine, options.requestBody, requestHeaders)
                res = connection.getresponse()
                resBody = res.read().decode("utf-8")
                resBodySize = len(resBody)
                isignored = False
                if options.ignoreText != None:
                    for igText in options.ignoreText:
                        if igText in resBody:
                            isignored = True

                if res.status >= 200 and res.status < 300:
                    if isignored == False and resBodySize >= options.dataLength:
                        print (' ' * len(strLine), "\r", end="")
                        printMSG("Code " + str(res.status) + " : " + targetPro+targetDomain+targetPath+pathLine + " (" + str(resBodySize) + " Byte)")
                        countFound += 1

                if options.showError != None:
                    if res.status >= 500 and res.status < 600:
                        if isignored == False and resBodySize >= options.dataLength:
                            print (' ' * len(strLine), "\r", end="")
                            printMSG("Code " + str(res.status) + " : " + targetPro+targetDomain+targetPath+pathLine)
                            countFound += 1

                if options.showRedirect != None:
                    if res.status >= 300 and res.status < 400:
                        if isignored == False and resBodySize >= options.dataLength:
                            print (' ' * len(strLine), "\r", end="")
                            printMSG("Code " + str(res.status) + " : " + targetPro+targetDomain+targetPath+pathLine + " ( " + res.getheader("location") + " )")
                            countFound += 1
        except Exception as ErrMs:
            if options.verbose != None:
                print (' ' * len(strLine), "\r", end="")
                printMSG("Error: " + str(ErrMs))
            try:
                connection.close()
                pass
            except Exception as e:
                if options.verbose != None:
                    printMSG("Error2:" + str(e))
                pass
            
        
    connection.close()
    print (' ' * len(strLine), "\r", end="")
    printMSG( "Total Pages found: " + str(countFound) )



if __name__ == "__main__":
    main()
