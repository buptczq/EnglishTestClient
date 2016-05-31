#!/usr/bin/evn python 
#coding:utf-8 
"""
A simple implement to parse paper.xml
By ZPCCZQ
"""
try: 
  import xml.etree.cElementTree as ET 
except ImportError: 
  import xml.etree.ElementTree as ET 
import sys 
  
#全局唯一标识  
unique_id = 1  
  
#遍历所有的节点  
def walkData(root_node, level, result_list):  
    global unique_id  
    temp_list =[unique_id, level, root_node.tag, root_node.attrib, root_node.text]  
    result_list.append(temp_list)  
    unique_id += 1  
      
    #遍历每个子节点  
    children_node = root_node.getchildren()  
    if len(children_node) == 0:  
        return  
    for child in children_node:  
        walkData(child, level + 1, result_list)  
    return  
  
def getXmlData(file_name):  
    level = 1 #节点的深度从1开始  
    result_list = []  
    root = ET.parse(file_name).getroot()  
    walkData(root, level, result_list)  
  
    return result_list  

def getAllQuestion(file_name):
    data=getXmlData(file_name)
    assessmentItems=[]
    state=0
    temp=None
    for x in data:
        if x[2]=="paper":
            pid=x[3]["identifier"]
        if state==0:
            if x[2]=="assessmentItem":
                if temp!=None:
                    if qtemp!=None:
                        temp["question"].append(qtemp)
                        assessmentItems.append(temp)
                temp={"question":[],"transcript":[]}
                qtemp=None
                continue
            if x[2]=="transcript":
                temp["transcript"].append(x[4])
                continue
            if x[2]=="question":
                if qtemp!=None:
                    temp["question"].append(qtemp)
                qtemp=x[3]
                qtemp["transcript"]=[]
                qtemp["options"]=[]
                state=1
                continue
        elif state==1:
            if x[2]=="transcript":
                qtemp["transcript"].append(x[4])
                continue
            if x[2]=="option":
                qtemp["options"].append((x[3]["id"],x[4]))
                continue
            if x[2]=="question":
                temp["question"].append(qtemp)
                qtemp=x[3]
                qtemp["transcript"]=[]
                qtemp["options"]=[]
                continue
            if x[2]=="assessmentItem":
                if qtemp!=None:
                  temp["question"].append(qtemp)
                assessmentItems.append(temp)
                temp={"question":[],"transcript":[]}
                qtemp=None
                state=0
                continue
    if qtemp!=None:
      temp["question"].append(qtemp)
    assessmentItems.append(temp)
    return (pid,assessmentItems)
