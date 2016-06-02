#!/usr/bin/env python 
#coding:utf-8
import os
import sys
import requests
import urllib
from qzip import unpack_qzip,pack_answer_qzip
from qxml import getAllQuestion
import re
import traceback
import json
import logging
import logging.handlers
           

def ascii_print(text):
    temp=""
    for i in text:
        if ord(i)<128 and ord(i)!=0:
            temp+=i
    print temp


def safe_print(text):
    try:
        print text
    except:
        ascii_print(text)

def input_answer(qdata):
    answer=[]
    a=1
    b=2
    c=3
    d=4
    n=1
    for item in qdata:
        # print section script
        for script in item["transcript"]:
            m = re.findall(r'[ub]>([^<^>.]+)</', script)
            safe_print(script)
        # print question and input answer
        for q in item["question"]:
            print "\nNO.%d"%n
            n+=1
            # print question script
            for script in q["transcript"]:
                safe_print(script)
            # print options
            for op in q["options"]:
                safe_print("%s. %s"%(op[0],op[1]))
            # input answer
            if q["type"]=='choice':
                # choice
                print "Your choice:"
                while True:
                    try:
                        temp=(q["type"],input())
                        break
                    except:
                        print "Error!"
                        print "Reinput your choice:"
                answer.append(temp)
            else:
                # text
                print "Input the word in <u><b>_____</b></u>(ENTER to skip):"
                if len(m)>0:
                    print m[0]
                    temp_in=raw_input()
                    if temp_in=="":
                        answer.append((q["type"],m[0]))
                    else:
                        answer.append((q["type"],temp_in))
                    m=m[1:]
                else:
                    answer.append((q["type"],raw_input()))
    return answer


try:
    os.chdir(os.path.dirname(sys.argv[0]))
except:
    pass

# logging
LOG_FILE = 'TestClient_Fake.log'
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes = 1024*1024, backupCount = 5)
fmt = '[%(asctime)s,%(filename)s:%(lineno)s]%(name)s:%(message)s'
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)
logger = logging.getLogger('TestClient')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# parse cmd args
try:
    testname=sys.argv[1]
    testserver=sys.argv[2]
    sid=sys.argv[3]
    paper=sys.argv[5]
    session=sys.argv[6]
except:
    logger.exception("ARGV Error.")
    os._exit(0)
logger.info("TestClient are being called.")
logger.info("CMD:"+" ".join(sys.argv))
# i only want to test A class
paper=paper.replace('-B.qzip','-A.qzip')
paper=paper.replace('-C.qzip','-A.qzip')
paper=paper.replace('-D.qzip','-A.qzip')
posturl = "npels/unittest/postanswer.aspx?answer="

# download paper
def Schedule(a,b,c):
    per = 100.0 * a * b / c
    if per > 100 :
        per = 100
    print 'Downloading: %.2f%%' % per
print "Download: ",testserver+paper
logger.info("Download: "+testserver+paper)
urllib.urlretrieve(testserver+paper,"paper.qzip",Schedule)
logger.info("Downloaded.")

# unpack paper
try:
    ret=unpack_qzip("paper.qzip")
except:
    logger.exception("unpack_qzip:fail.")
    print "unpack_qzip:fail"
    os._exit(0)

# get questions
pid, qdata=getAllQuestion("paper.xml")
print "----------------------"
print "Begin the test!"
print "Load paper:",pid
print "File:",paper
print "----------------------"
for i in range(3):
    print "                     "
# read answers
loadjson=None
try:
    with open("%s.ans"%pid,"r") as fi:
        loadjson=json.loads(fi.read())
except:
    pass

# make some answers wrong
if loadjson!=None:
    logger.info("Load answer file:%s.ans"%pid)
    answer=loadjson
    print "How many errors would you want?"
    nwrong=input()
    logger.info("user inputed:%d errors"%nwrong)
    for i in range(nwrong):
        if answer[i][0]=='choice':
            answer[i][1]=answer[i][1]-1
            if answer[i][1]==0:
                answer[i][1]=2
        else:
            answer[i][1]=""
else:
    # answer questions
    try:
        answer=input_answer(qdata)
    except:
        traceback.print_exc()
        logger.exception("unpack_qzip:fail.")
        print "Please push ENTER to exit."
        raw_input()
        os._exit(0)
    print "Save answers to %s.ans"%pid
    with open("%s.ans"%pid,"w") as fw:
        fw.write(json.dumps(answer))

answer_post=pack_answer_qzip(answer,pid,sid)
print "ID\tAnswer"
n=1
for x in answer:
    print "%s\t%s"% (n,x[1])
    n+=1
print "Please push ENTER to confirm."
raw_input()
# post answer data
postdata="-----HTTP-DATA-BOUNDARY-14664\r\n"
postdata+='''Content-Disposition: form-data; name="action"\r\n\r\n.\r\n'''
postdata+='''-----HTTP-DATA-BOUNDARY-14664\r\n'''
postdata+='''Content-Disposition: form-data; name="answer"\r\n'''
postdata+='''Content-Type: application/octet-stream\r\n\r\n'''
postdata+=answer_post
postdata+='''\r\n-----HTTP-DATA-BOUNDARY-14664\r\n'''
postdata+='''Content-Disposition: form-data; name="classid"\r\n\r\n'''
postdata+=session
postdata+='''\r\n-----HTTP-DATA-BOUNDARY-14664\r\n'''
postdata+='''Content-Disposition: form-data; name="paperpath"\r\n\r\n'''
postdata+=paper
postdata+='''\r\n-----HTTP-DATA-BOUNDARY-14664--\r\n'''
headers = {'content-type': 'multipart/form-data; boundary=---HTTP-DATA-BOUNDARY-14664'}
print "Posting..."
post_ret=requests.post(testserver+posturl, data=postdata, headers=headers)
logger.info("POST %s"%(testserver+posturl))
logger.info("HEAD %s"%json.dumps(headers))
logger.info("DATA %s"%postdata)
logger.info("RET %s"%post_ret.status_code)
logger.info("Test end.")
print "Posted answer!"
print "Please push ENTER to exit."
raw_input()
