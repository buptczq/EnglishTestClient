"""
A simple implement to pack&unpack qzip file.
By ZPCCZQ
"""
import struct
import time
import zlib
from crc16 import crc16 as qChecksum

dir_name="AGEAbgBzAHcAZQBy"
file_name="AGEAbgBzAHcAZQByAC4AeABtAGw="
xml_data='''<?xml version='1.0'?>
<answer paperId="{{pid}}" examineeId="" completeTime="{{endtime}}" examineeName="{{sid}}" studentId="{{sid}}" startTime="{{starttime}}">
{{answer}}
</answer>'''

CRCTable =(0x0000, 0x1081, 0x2102, 0x3183, 0x4204, 0x5285, 0x6306, 0x7387, 0x8408, 0x9489, 0xa50a, 0xb58b, 0xc60c, 0xd68d, 0xe70e, 0xf78f,)

def qCompress(data):
    return struct.pack(">I",len(data))+zlib.compress(data)

def qUncompress(data):
    return zlib.decompress(data[4:])

def pack_answer_qzip(answer,pid,sid):
    sdir_name=dir_name.decode("base64")
    qzip_data=struct.pack('!I',len(sdir_name))
    qzip_data+=sdir_name
    qzip_data+=struct.pack('!I',1)
    sfile_name=file_name.decode("base64")
    qzip_data+=struct.pack('!I',len(sfile_name))
    qzip_data+=sfile_name
    
    xml_answer=""

    qxml=xml_data
    qxml=qxml.replace("{{pid}}",pid)
    qxml=qxml.replace("{{sid}}",sid)
    qxml=qxml.replace("{{starttime}}",str(int(time.time())))
    qxml=qxml.replace("{{endtime}}",str(int(time.time()+2400)))
    for qtype,ans in answer:
        if qtype=="choice":
            xml_answer+="    <value>\n"
            xml_answer+="        <choice>%d</choice>\n"%ans
            xml_answer+="    </value>\n"
        else:
            xml_answer+="    <value>\n"
            xml_answer+="        <text>%s</text>\n"%ans
            xml_answer+="    </value>\n"
    qxml=qxml.replace("{{answer}}",xml_answer)
    xmldata_compress=qCompress(qxml)
    xmldata_crc=qChecksum(xmldata_compress)
    qzip_data+=struct.pack('!I',len(xmldata_compress))
    qzip_data+=xmldata_compress
    qzip_data+=struct.pack('!H',xmldata_crc)
    xmldata_crc=qChecksum(qzip_data)
    qzip_data=struct.pack('!H',xmldata_crc)+qzip_data
    return qzip_data.encode("base64")

def unpack_qzip(filename,check_crc=True):
    fp = open(filename,"rb")
    rdata=fp.read()
    if len(rdata)<2:
        raise Exception, "bad qzip file!"
    checksum=ord(rdata[0])*16*16+ord(rdata[1])
    if check_crc and qChecksum(rdata[2:])!=checksum:
        raise Exception, "bad qzip file!"
    dirnamelen=struct.unpack("!I",rdata[2:6])[0]
    dirname=rdata[6:6+dirnamelen].replace("\x00","")
    filenumber=struct.unpack("!I",rdata[6+dirnamelen:6+dirnamelen+4])[0]

    allfiles=[]
    pbegin=6+dirnamelen+4
    for i in range(filenumber):
        lenofname=struct.unpack("!I",rdata[pbegin:pbegin+4])[0]
        allfiles.append(rdata[pbegin+4:pbegin+4+lenofname].replace("\x00",""))
        pbegin=pbegin+4+lenofname
    for i in range(filenumber):
        compressdata=rdata[pbegin:]
        filelen=struct.unpack("!I",compressdata[0:4])[0]
        tempdata=compressdata[4:4+filelen]
        checkcode=ord(compressdata[4+filelen])*16*16+ord(compressdata[4+filelen+1])
        assert qChecksum(tempdata)==checkcode
        with open(allfiles[i].replace("/","_"),"wb") as fo:
            fo.write(qUncompress(tempdata))
        if allfiles[i].replace("/","_")=="paper.xml":
            break
        pbegin=pbegin+4+filelen+2
    fp.close()
    return 0
