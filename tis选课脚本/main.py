import requests
import time
from random import *
from re import findall
from json import load
from os import path
import _thread

def caslogin(userName,passWord):
    loginUrl="https://cas.sustech.edu.cn/cas/login?service=https%3A%2F%2Ftis.sustech.edu.cn%2FcasLogin"
    req=requests.get(loginUrl)
    if(req.status_code == 200):
        print("成功连接到CAS...")
    else:
        print("请检查您的网络连接状态")
        return "",""
    data = {
        'username': userName,
        'password': passWord,
        'execution': str(req.text).split('''name="execution" value="''')[1].split('"')[0],
        '_eventId': 'submit',
    }
    req=requests.post(loginUrl, data=data, allow_redirects=False)
    if("Location" in req.headers.keys()):
        print("登录成功...")
    else:
        print("用户名或密码错误，请检查")
        return "",""
    req=requests.get(req.headers["Location"], allow_redirects=False)
    route=findall('route=(.+?);', req.headers["Set-Cookie"])[0]
    JSESSIONID=findall('JSESSIONID=(.+?);', req.headers["Set-Cookie"])[0]
    return route,JSESSIONID
    
def submit(route,JSESSIONID,id):
    headers = {
        "cookie": 'route={}; JSESSIONID={};'.format(route,JSESSIONID),
        "user-agent": "Mozilla/5.0",
        "x-requested-with": "XMLHttpRequest"
    }
    data = {
        "p_xktjz": "rwtjzyx",#rwtjzgwc提交至购物车，rwtjzyx提交至已选 gwctjzyx购物车提交至已选
        "p_xn": "2020-2021",#学年
        "p_xq": 2,#学期
        "p_xkfsdm": "bxxk",#补选选课
        "p_id":id #课程id
        }
    req = requests.post('https://tis.sustech.edu.cn/Xsxk/addGouwuche',data=data,headers=headers)
    t=req.text 
    print(t)

if __name__ =='__main__':
    classData = {}
    cachePath = "userCache.json"
    if path.exists(cachePath) and path.isfile(cachePath):
        print("读取课程信息...")
        with open(cachePath, "r", encoding="utf8") as f:
            classData = load(f)["classData"][0]
            f.close()
        print("课程信息读取完毕...")
    else:
       print("课程信息丢失，请检查")
       exit(1)
    cachePath = "Class.txt"
    classList = []
    if path.exists(cachePath) and path.isfile(cachePath):
        print("读取规划课表...")
        with open(cachePath, "r", encoding="utf8") as f:
            classList = f.readlines();
        print("规划课表读取完毕...")
    else:
        print("没有找到规划课表，请手动输入课程信息，输入-1结束录入")
        while(True):
            s=input()
            if(s=="-1"):
                break
            else:
                classList.append(s)
        s=input("是否保存录入的信息（Y/N）？")
        if(s=="Y" or s=="y"):
            with open(cachePath, "w", encoding="utf8") as f:
                f.write("===本文件是待选课程的列表，一行输入一个课程名字==请勿删除本行===\n");
                for i in classList:
                    f.write(i+"\n")
                f.close()
    postList = []
    for name in classList:
        name=name.strip()
        if (name in classData.keys()) :
            postList.append(classData[name])
            print(name)
    print("成功读入以上信息")
    route,JSESSIONID="",""
    while(route=="" or JSESSIONID==""):
        userName=input("请输入您的学号：")
        passWord=input("请输入CAS 密码：")
        route,JSESSIONID=caslogin(userName,passWord)
        if(route=="" or JSESSIONID==""):
            print("请重试...")
    while(True):
        input("按任意键选课")
        for id in postList :
            try:
                _thread.start_new_thread(submit,(route,JSESSIONID,id) )
            except:
                print ("线程异常")
