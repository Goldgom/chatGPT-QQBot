# -*- coding:utf-8 -*-
#引用库
import threading
import re
import requests
import socket
import json
import traceback
from typing import List
from math import *
from PIL import Image
import encoder

#openai初始化
import openai
openai.api_key = "YOUR_API_KEY"
#设置管理员
admin = 0#设置管理员
#设置群
AIgroups = [1,2] #设置需要回应的qq群号
# 正则表达式
rePic = r"gchatpic_new/(.*?)\]"
reAt = r"\[CQ:at,qq=10086\] |@机器人 "#来这里设置你的匹配消息方式
reDraw = r"#绘画"
promptWords = [
    [{"role": "system", "content": "你是一个笨笨的机器人"}],
    [{"role": "system", "content": "你是一个憨憨机器人"}]

    ]#为每个群指定消息栈。注意这里列表的数量要和AIgroup的len匹配
#返回一句话的token数量
def getToken(text):
    enc = encoder.get_encoder()
    return len(enc.encode(text))
#返回对话的总token
def getTokens(n):
    global promptWords
    sum = 0
    for i in promptWords[n]:
        sum = sum + getToken(i['content'])
    return sum
#寻找从上到下最近的system位置
def findSystem(n):
    global promptWords
    sum = 0
    for i in promptWords[n]:
        if i["role"] == "system":
            return sum
        else:
            sum = sum + 1
#删除从上到下最近的system
def delSystem(n):
    global promptWords
    del promptWords[n][findSystem(n)]
#控制台打印某个对话所有消息
def printPromptWords(n):
    global promptWords
    for i in promptWords[n]:
        print("role:{}  content:{}\n".format(i['role'],i['content']))
#删除所有非system消息
def delMessages(n):
    global promptWords
    textPositions = []
    for i in range(0,len(promptWords[n])):
        if promptWords[n][i]['role'] == 'system':
            continue
        else:
            textPositions.append(i)
    for i in textPositions[::-1]:
        del promptWords[n][i]
    #printPromptWords(n)
#聊天接口，n表示指定对话线程
def AIchat(msg,n):
    global promptWords
    #特殊功能识别
    if msg == "#清除历史消息":
        delMessages(n)
        return "清除成功"
    #tokens超长判断
    tokenCount = getTokens(n)
    while getTokens(n) >= 4000:
        print("limited length")
        if promptWords[n][0]['role'] == 'system':
            del promptWords[n][1]
            del promptWords[n][1]
        else:
            del promptWords[n][0]
            del promptWords[n][0]
        tokenCount = getTokens(n)
    #system置底
    sysPosition = findSystem(n)
    print("system position = {}".format(sysPosition))
    if len(promptWords[n]) - sysPosition >= 4:
        print("sys changed")
        temp = promptWords[n][sysPosition]['content']
        delSystem(n)
        promptWords[n].insert(-4, {"role": "system", "content": temp})
        temp = 0
        #printPromptWords(n)
    #创建请求
    promptWords[n].append({"role": "user", "content":msg})
    print("linking to openai.com")
    res=openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=promptWords[n],
    temperature=1,
    )
    #请求处理
    print("linked to openai.com")
    if res['choices'][0]['finish_reason'] == "stop":
        
        promptWords[n].append(res['choices'][0]['message'])
        
        return res['choices'][0]['message']['content']
    elif res['choices'][0]['finish_reason'] == "content_filter":
        return "这是碰都不能碰的滑梯！快闭嘴"
    elif res['choices'][0]['finish_reason'] == "length":
        del (promptWords[n])[1]
        del (promptWords[n])[1]
        promptWords[n].pop()
        return AIchat(msg,n) 
    elif res['choices'][0]['finish_reason'] == "null":
        pass
    else:
        return "unexpected error occured"
    
#AI制图    
def AICreatePic(s):
    response = openai.Image.create(
    prompt=s,
    n=1,
    size="1024x1024"
    )
    image_url = response['data'][0]['url']
    return image_url
def AIreCreatePic(s):
    response = openai.Image.create_variation(
    image=open(s, "rb"),
    n=1,
    size="1024x1024"
    )
    image_url = response['data'][0]['url']
    return image_url


# 基础发送消息函数

def sendMsg(msg,qq_type="group", id=0):
    if qq_type == "private":
        data = {
            'user_id': id,
            'message': msg,
            'auto_escape': False
        }
        cq_url = "http://127.0.0.1:5700/send_private_msg"
    elif qq_type == "group":
        data = {
            'group_id': id,
            'message': msg,
            'auto_escape': False
        }
        cq_url = "http://127.0.0.1:5700/send_group_msg"
    else:
        return False
    requests.post(cq_url, data=data)


# 基础获取群人员列表


def getGroup(id):
    date = []
    response = requests.post(
        'http://127.0.0.1:5700/get_group_member_list?group_id='+str(id)).json()
    for i in response['data']:
        temp = ""
        if(i['card'] != ''):
            temp = i['card']  # +str(i['user_id'])
        else:
            temp = i['nickname']  # +str(i['user_id'])
        date.append(temp)
    return date


# 基础撤回消息


def delMsg(msgid):
    data = {
        'message_id': msgid
    }
    cq_url = "http://127.0.0.1:5700/delete_msg"
    requests.post(cq_url, data=data)


# 基础禁言功能


def ban(group_id,user_id,time):
    data = {
        'user_id': user_id,
        'group_id': group_id,
        'duration':time
    }
    cq_url = "http://127.0.0.1:5700/set_group_ban"
    requests.post(cq_url, data=data)    

# 全员禁言
def banall(group_id,enable):
    if enable == "true":
        data = {
            "enable": "true",
            'group_id': group_id
        }
    else:
        data = {
            "enable": "false",
            'group_id': group_id
        }
    cq_url = "http://127.0.0.1:5700/set_group_whole_ban"
    requests.post(cq_url, data=data)    


# 踢人
def kick(group_id,user_id):
    data = {
        "user_id": user_id,
        'group_id': group_id
    }
    cq_url = "http://127.0.0.1:5700/set_group_kick"
    requests.post(cq_url, data=data)  

# 消息接收部分


encoding = 'utf-8'
BUFSIZE = 1024
temp = ""

# a read thread, read data from remote

class Reader(threading.Thread):
    global temp

    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client

    def run(self):
        global temp
        while True:
            data = self.client.recv(BUFSIZE)
            if(data):
                temp = bytes.decode(data, encoding)
            else:
                break

    def readline(self):
        rec = self.inputs.readline()
        if rec:
            string = bytes.decode(rec, encoding)
            if len(string) > 2:
                string = string[0:-2]
            else:
                string = ' '
        else:
            string = False
        return string


# a listen thread, listen remote connect
# when a remote machine request to connect, it will create a read thread to handle

class Listener(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", port))
        self.sock.listen(1)

    def run(self):
        print("listener started")
        while True:
            client, cltadd = self.sock.accept()
            Reader(client).start()
            cltadd = cltadd


#消息监听


lst = Listener(25567)   # create a listen thread
lst.start()  # then start


# 消抖


msgidTemp = []
increaseTemp = []
msgTemp = []
#循环监听

while True:

    #防止溢出

    if len(msgidTemp) > 50:
        msgidTemp = msgidTemp[25:]
    if len(msgidTemp) > 50:
        increaseTemp = increaseTemp[25:]
    if len(msgTemp) > 50:
        msgTemp = msgTemp[25:]

    #忽略所有异常保证程序稳定性

    try:
        if temp != "":
            temp = str(temp)
            temp = temp[24*7:]
            rev = json.loads(temp)
            
            #新生欢迎
            if rev["message_type"] == "group":
                if rev["group_id"] in AIgroups:
                    print("**************************\nmaybe it need an AI")
                    if rev["post_type"] == "message":

                        #信息处理

                        msg = rev["message"]
                        msgid = rev["message_id"]
                        time = int(rev["time"])
                        user_id = rev["user_id"]
                        role = rev["sender"]["role"]
                        if rev["sender"]["card"] == "":
                            name = rev["sender"]["nickname"]
                        else:
                            name = rev["sender"]["card"]
                        print("get message")
                        if msgid not in msgidTemp:
                            print("收到一条新消息")
                            print(temp)
                            msgidTemp.append(msgid)
                            if re.match(reAt , msg) != None: 
                                msg = re.sub(reAt,"",msg)
                                if re.match(reDraw , msg) != None:
                                    msg = re.sub(reDraw,"",msg)
                                    if msg != "":
                                        print("drawing:{}".format(msg))
                                        picUrl = AICreatePic(msg)
                                        sendMsg("[CQ:image,file={}]".format(picUrl),id=rev["group_id"],qq_type="group")
                                elif "https://gchat.qpic.cn/gchatpic_new/" in msg:
                                    url = "https://gchat.qpic.cn/gchatpic_new/" + re.findall(rePic,msg)[0]
                                    sendMsg(url,id=admin,qq_type="private")
                                    print("rePainting:{}".format(url))
                                    r = requests.get(url)
                                    with open("demo.jpg", "wb") as i:
                                        i.write(r.content)
                                    im = Image.open("demo.jpg")
                                    x, y = im.size
                                    imb = Image.open("bg.png")
                                    image = Image.new('RGB', (1024,1024), (0,0,0))
                                    if x>=y:
                                        im = im.resize((1024,int(1024/x*y)),Image.ANTIALIAS)
                                        image.paste(im,(0,512-int(512/x*y))) 
                                    else:
                                        im = im.resize((int(1024*x/y),1024),Image.ANTIALIAS)
                                        image.paste(im,(512-int(512*x/y),0)) 
   
                                    image.save("demo.png")
                                    sendMsg("[CQ:image,file={}]".format(AIreCreatePic("demo.png")),id=rev["group_id"],qq_type="group")
                                else:
                                    print("talking")
                                    sendMsg("[CQ:at,qq={}] {}".format(user_id,AIchat(msg,AIgroups.index(rev["group_id"]))),id=rev["group_id"],qq_type="group")

    except:
        error=traceback.format_exc()
        print(error)
        if "json.decoder.JSONDecodeError" not in error:
            if "KeyError: 'message_type'" not in error:
                sendMsg(error,admin,qq_type="private")
        continue

