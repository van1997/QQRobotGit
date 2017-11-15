import requests
from qqbot import QQBotSlot,RunBot
import json
import time
import pymysql
import re
from prettytable import PrettyTable


startime=time.time()            #发言计时开始时间，用于刷屏禁言
endtime=time.time()+3            #发言计时结束时间，用于刷屏禁言
count={}                         #发言计数，用于刷屏禁言
signInMember={}                    #签到人员
dbConfig={}                        #数据库配置
apiConfig={}                    #聊天机器人接口配置

def parseJson():
    f=open('config.json','r',encoding='utf-8')
    text=f.read()
    return json.loads(text)

def increasePoints(qqNumber,points):
    db = pymysql.connect(host=dbConfig['host'],user=dbConfig['user'],passwd=dbConfig['passwd'],db=dbConfig['db'], charset=dbConfig['charset'])
    cursor = db.cursor()
    cursor.execute('UPDATE signpoints SET points=points+(%S)  WHERE qqnumber=(%s)',(str(points),str(qqNumber)))
    db.commit()
    cursor.close()
    db.close()

def queryPoints(qqNumber):
    db = pymysql.connect(host=dbConfig['host'],user=dbConfig['user'],passwd=dbConfig['passwd'],db=dbConfig['db'], charset=dbConfig['charset'])
    cursor = db.cursor()
    cursor.execute('SELECT points FROM signpoints WHERE qqnumber=(%s)',(str(qqNumber)))
    data =cursor.fetchone()
    cursor.close()
    db.close()
    return data[0]

def pointsTable(content,bot,contact):
    table = PrettyTable(["姓 名", "积 分","排 名"])
    table.align["姓 名"] = "l"
    table.align["积 分"] = "l"
    table.align["排 名"] = "l"
    table.padding_width = 1
    info={}
    for person in signInMember:
        info[person['name']]=queryPoints(person['number'])
    infoList=sorted(info.items(),key=lambda item:item[1],reverse = True)

    exsistName=False

    for i in range(len(infoList)):
        if infoList[i][0] in content:
            table.add_row([infoList[i][0],str(infoList[i][1]),str(i+1)])
            exsistName=True
    if exsistName is False :
        if re.match(r'.*查询.+积分.*',content):
            bot.SendTo(contact,'未在签到列表中找到该人，正在为你查询所有人的积分...'.encode('utf-8'))
        for i in range(len(infoList)):
            table.add_row([infoList[i][0],str(infoList[i][1]),str(i+1)])
    return table

def signInRank(date,qqNumber):
    db = pymysql.connect(host=dbConfig['host'],user=dbConfig['user'],passwd=dbConfig['passwd'],db=dbConfig['db'], charset=dbConfig['charset'])
    cursor = db.cursor()
    cursor.execute('SELECT * FROM signinrank WHERE date=(%s) and qqnumber=(%s)',(date,str(qqNumber)))
    
    if len(cursor.fetchall())!=0:
        cursor.close()
        db.close()
        return -1
    else:
        cursor.execute('SELECT * FROM signinrank WHERE date=%s',(date))
        signAmount=len(cursor.fetchall())
        cursor.execute('INSERT INTO signinrank (date,rank,qqnumber) values (%s,%s,%s)',(date,str(signAmount+1),str(qqNumber)))
        db.commit()
        cursor.close()
        db.close()
        return signAmount+1

def signIn(bot,contact,member):
    currentHour=time.localtime(time.time())[3]
    name=''
    for person in signInMember:
        if person['number']==int(member.qq):
            name=person['name']
    
    if name=='':
        bot.SendTo(contact,'不在签到列表中'.encode('utf-8'))

    elif currentHour <0:    #currentHour>=9 or currentHour<=7:
        bot.SendTo(contact,'现在不是签到时间'.encode('utf-8'))

    else:
        try:
            date=time.strftime("%Y%m%d", time.localtime())
            rank=signInRank(date,int(member.qq))
            if rank==-1:
                bot.SendTo(contact,'今天已签到'.encode('utf-8'))
                return
            points=6-rank
            if (6-rank)>0:
                increasePoints(int(member.qq),points)
                bot.SendTo(contact,('签到成功！'+name+'，你是今天第'+str(rank)+'个签到的！已加积分：'+str(6-rank)+'分\r\n正在为你查询当前积分...').encode('utf-8'))
                bot.SendTo(contact,str(pointsTable(name,bot,contact)).encode('utf-8'))
            else:
                bot.SendTo(contact,('签到成功！'+name+'，你是今天第'+str(rank)+'个签到的！前五个签到的人才有积分，继续努力！').encode('utf-8'))
        except Exception as  e:
            #print(str(e))
            bot.SendTo(contact,'服务器好像开小差了...'.encode('utf-8'))     

def shut(bot,contact,member,warn):
    bot.GroupShut(group, membs, 60)
    bot.SendTo(contact,warn.encode('utf-8'))

@QQBotSlot
def onQQMessage(bot,contact,member,content):
    global startime
    global endtime
    global count
    global signInMember
    global dbConfig
    global apiConfig

    qqNumber=int(contact.qq)                                    #当前联系人qq
    config=parseJson()                                            #加载配置文件
    dbConfig=config['dbConfig']                                    #数据库配置
    apiConfig=config["apiConfig"]                                #聊天机器人接口配置
    replyList=config['replyList']                                #开启自动回复的联系人列表
    keywordList=config['keywordList']                            #特定关键词以及回复列表
    signInList=config['signInList']                                #开启签到以及积分查询功能的联系人列表
    signInMember=config['signInMember']                            #签到成员列表
    shutList=config['shutList']                                    #开启禁言功能的群列表
    newsList=config['newsList']                                    #开启推送新闻功能的群列表
    someoneReplyList=config['someoneReplyList']                 #特定联系人关键词回复列表

    if isIn(qqNumber,signInList,"number"):                        #在这些群中开启签到和积分功能
        if content=='签到':                                #re.match(r'^(?!(.*?今天.*?)).*签到(?!成功).*',content):
            if '我' in content:
                name=''
                for person in signInMember:
                    if person['number']==int(member.qq):
                        name=person['name']
                        content=content+name
                if name=='':
                    bot.SendTo(contact,'你不在签到列表中，无法查询积分'.encode('utf-8'))
            signIn(bot,contact,member)
            return

        if re.match(r'(?!.*正在为你).*(查询|查一下).*积分.*',content) or re.match(r'.*积分.*查询.*',content):
            bot.SendTo(contact,str(pointsTable(content,bot,contact)).encode('utf-8'))
            return

    if isIn(qqNumber,shutList,"number"):                        #在这些群开启刷屏禁言功能
        memberNumer=int(member.qq)
        if bot.isMe(contact,member) is False:
            currenttime=time.time()
            if currenttime<endtime :
                if (memberNumer in count.keys()) is False:
                    count[qqNumber][memberNumer]=1
                else:
                    count[qqnumber][member.qq]=count[qqnumber][memberNumer]+1
            else:
                startime=currenttime
                endtime=currenttime+3
                if memberNumer in count.keys():
                    if count[qqnumber][memberNumer]>8:
                        shut(bot,contact,member,'本群禁止刷屏')
                        for key in count.keys():
                            key=0
                        return
                for item in count.keys():
                    for person in count[item]:
                        count[item][person]=0

    if isIn(qqNumber,replyList,"number"):                        #在这些联系人中开启自动回复功能
        if member is not None:                                   #在QQ群中开启特定联系人关键词回复功能
            if isIn(int(member.qq),someoneReplyList,"number"):
                for item in someoneReplyList:
                    if item['number']==int(member.qq):
                        if item['pattern']=='appro':            #模糊匹配
                            if item['keyword'] in content:
                                bot.SendTo(contact,item['answer'].encode('utf-8'))
                        elif item['pattern']=='accur':           #精确匹配
                            if item['keyword']==content:
                                bot.SendTo(contact,item['answer'].encode('utf-8'))
                return
        
        if isIn(content,keywordList,"keyword"):                  #在QQ群中开启特定关键词回复功能
            for item in keywordList:
                if item['keyword']==content:
                    bot.SendTo(contact,item['answer'].encode('utf-8'))
                    return

        if (bot.isMe(contact, member) is False):
            bot.SendTo(contact,answer(content,contact).encode('utf-8'))

def isIn(index,list,key):                        #判断index是否在list中,即是否等于list中的某个字典的以key为键的value
    for item in list:
        if item[key]==index:
            return True
    return False

def answer(content,contact):
    serviceApi=apiConfig["serviceApi"]
    data={
        'key':apiConfig["key"],
        'info':content,
        'userid':contact.qq
    }
    text=requests.post(serviceApi,data).text
    return json.loads(text)['text']

if __name__=='__main__':
    RunBot()
