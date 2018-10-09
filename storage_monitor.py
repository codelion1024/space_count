#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import datetime
import commands
import subprocess
import json
import requests
import smtplib
import fileinput
import mimetypes


# the path to save json data file
jsonpath = "~/.storagemonitordata"
global usedsize

from email import Charset
from email import encoders
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
ToList = ['test1@example.com']
CcList = ['test2@example.com']
def mailNotify(title, jsonfile):
    title="json file upload FAILED!!!:" + title
    fp = open(jsonfile, 'rb')
    body = fp.read()
    fp.close()
    Charset.add_charset('utf-8', Charset.QP, Charset.QP)
    msg = MIMEText(body, _charset='utf-8')
    msg['Subject'] = title
    msg['From'] = 'test3@example.com'
    msg['To'] = ', '.join( ToList )
    msg['Cc'] = ', '.join( CcList )
    s = smtplib.SMTP()
    s.connect("mail.srv")
    s.ehlo("hello")
    s.sendmail('test4@example.com', ToList+CcList, msg.as_string())
    s.close()
    print "json file upload failed,send notify mail done."

def scanFiles(folder, partitionflag):
    global usedsize
    files = os.listdir(folder)
    files.sort()
    for fileName in files:
        if not os.path.islink(folder + '/' + fileName):
            if os.path.isdir(folder + '/' + fileName):
                print >> json, "    {"
                dirsize = commands.getoutput('stat -c %s ' + folder + '/' + fileName)
                usedsize = usedsize + int(dirsize)
                if partitionflag == "cust":
                    dirpath = folder[1:].replace("CUST", "cust", 1) + "/" + fileName
                elif partitionflag == "data":
                    dirpath = folder[1:].replace("DATA", "data", 1) + "/" + fileName
                elif partitionflag == "system":
                    dirpath = folder[1:] + "/" + fileName

                print >> json, "      \"file_path\":\"%s\","  %dirpath
                print >> json, "      \"file_size\":\"%s\","  %dirsize
                print >> json, "      \"file_type\":\"dir\""
                print >> json, "    },"
                scanFiles(folder + '/' + fileName, partitionflag)
            else:
                print >> json, "    {"
                filesize = commands.getoutput('stat -c %s ' + folder + '/' + fileName)
                usedsize = usedsize + int(filesize)
                if partitionflag == "cust":
                    filepath = folder[1:].replace("CUST", "cust", 1) + "/" + fileName
                elif partitionflag == "data":
                    filepath = folder[1:].replace("DATA", "data", 1) + "/" + fileName
                elif partitionflag == "system":
                    filepath = folder[1:] + "/" + fileName

                print >> json, "      \"file_path\":\"%s\","  %filepath
                print >> json, "      \"file_size\":\"%s\","  %filesize
                print >> json, "      \"file_type\":\"file\""
                print >> json, "    },"


server_file = open(sys.argv[1])
for line in server_file.readlines():
    line = line.strip('\n')
    keyvalue = line.split(' ')
    if (keyvalue[0] == "path_to_out"):
        outdir = keyvalue[1]
    elif (keyvalue[0] == "target_product"):
        device_name = keyvalue[1]
    elif (keyvalue[0] == "success"):
        build_success = keyvalue[1]
server_file.close()

time_stamp = datetime.datetime.now()
jsonfilestr = jsonpath + "/" + device_name + "-" + "_" + time_stamp.strftime('%Y.%m.%d-%H:%M:%S') + ".json"
miscinfostr = jsonpath + "/" + device_name + "-" + "_" + time_stamp.strftime('%Y.%m.%d-%H:%M:%S') + ".txt"
objdir = outdir + "/obj/PACKAGING/target_files_intermediates/" + device_name + "-target_files-"
system_total = 0
data_total = 0



cust_total = "none"
metainfo_file = open(objdir + "/META/misc_info.txt")
for line in metainfo_file.readlines():
    line = line.strip('\n')
    keyvalue = line.split('=')
    if (keyvalue[0] == "system_size"):
        system_total = keyvalue[1]
    elif (keyvalue[0] == "userdata_size"):
        data_total = keyvalue[1]
    if (has_cust == "true"):
        if (keyvalue[0] == "cust_size"):
            cust_total = keyvalue[1]
metainfo_file.close()

if not os.path.exists(jsonpath):
    os.makedirs(jsonpath)
if os.path.exists(jsonfilestr):
    os.remove(jsonfilestr)
if os.path.exists(miscinfostr):
    os.remove(miscinfostr)


json = open(jsonfilestr,'w')
print >> json, "{"
print >> json, "  \"ts\":\"%s\","       %time_stamp.strftime('%Y.%m.%d-%H:%M:%S')
print >> json, "  \"success\":\"%s\","  %build_success
print >> json, "  \"name\":\"%s\","     %device_name
print >> json, "  \"type\":\"%s\","     %version_type
print >> json, "  \"files\":["


# scan data partition
os.chdir(objdir)
usedsize=0
scanFiles("./DATA", "data")
data_used = usedsize

# scan system partition
os.chdir(outdir)
usedsize=0
scanFiles("./system", "system")
system_used = usedsize


json.flush()
# according to json format,change the last elemnet's format form "}," to "}"
(result, output)=commands.getstatusoutput('sed -i \'$d\' ' + jsonfilestr)
json.close()
json = open(jsonfilestr,'a')
print >> json, "    }"
print >> json, "  ],"
print >> json, "  \"st\":\"%s\","   %system_total
print >> json, "  \"su\":\"%s\","   %system_used
print >> json, "  \"dt\":\"%s\","   %data_total
print >> json, "  \"du\":\"%s\","   %data_used
print >> json, "  \"ct\":\"%s\","   %cust_total
print >> json, "  \"cu\":\"%s\""    %cust_used
print >> json, "}"
json.close()


curloutput = commands.getoutput('curl -X POST -H \"\'Content-type\':\'application/json\', \'charset\':\'utf-8\'\" http://xxx/partitionUpload --data-binary @' + jsonfilestr)
print curloutput
if curloutput.find('200') == -1:
    mailtitle = jsonpath + "/" + device_name + "-" + miui_version + "_" + is_global + "_" + time_stamp.strftime('%Y.%m.%d-%H:%M:%S')
    mailNotify(mailtitle, jsonfilestr)
else:
    print "curl post ok"

miscinfo = open(miscinfostr,'w')
print >> miscinfo, "time_stamp       " + time_stamp.strftime('%Y.%m.%d-%H:%M:%S')
print >> miscinfo, "outdir           " + outdir
print >> miscinfo, "device_name      " + device_name
print >> miscinfo, "version_type     " + version_type
print >> miscinfo, "build_success    " + build_success
print >> miscinfo, "jsonfilestr      " + jsonfilestr
print >> miscinfo, "miscinfostr      " + miscinfostr
print >> miscinfo, "objdir           " + objdir
print >> miscinfo, "system_total     " + system_total
print >> miscinfo, "system_used      " + str(system_used)
print >> miscinfo, "data_total       " + data_total
print >> miscinfo, "data_used        " + str(data_used)
miscinfo.close()

