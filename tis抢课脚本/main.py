import requests
from json import loads
from getpass import getpass
from re import findall
from os import path
import _thread
from colorama import init

init(autoreset=True)
xueNian = "2021-2022"
xueQi = 1
xueNianXueQi = xueNian+str(xueQi)

def caslogin(token, userName, passWord):
    print("[\x1b[0;36m!\x1b[0m] " + "测试CAS链接...")
    try:
        loginUrl = "https://cas.sustech.edu.cn/cas/login?service=https%3A%2F%2Ftis.sustech.edu.cn%2Fcas"  # removed Login
        req = token.get(loginUrl)
        assert (req.status_code == 200)
        print("[\x1b[0;32m+\x1b[0m] " + "成功连接到CAS...")
    except:
        print("[\x1b[0;31mx\x1b[0m] " + "不能访问CAS, 请检查您的网络连接状态")
        return "", ""
    print("[\x1b[0;36m!\x1b[0m] " + "登录中...")
    data = {
        'username': userName,
        'password': passWord,
        'execution': str(req.text).split('''name="execution" value="''')[1].split('"')[0],
        '_eventId': 'submit',
    }
    req = token.post(loginUrl, data=data, allow_redirects=False)
    if "Location" in req.headers.keys():
        print("[\x1b[0;32m+\x1b[0m] " + "登录成功")
    else:
        print("[\x1b[0;31mx\x1b[0m] " + "用户名或密码错误，请检查")
        return "", ""
    req = token.get(req.headers["Location"], allow_redirects=False)
    route = findall('route=(.+?);', req.headers["Set-Cookie"])[0]
    JSESSIONID = findall('JSESSIONID=(.+?);', req.headers["Set-Cookie"])[0]
    return route, JSESSIONID


def getinfo(route, JSESSIONID):
    headers = {
        "cookie": 'route={}; JSESSIONID={};'.format(route, JSESSIONID),
        "user-agent": "Mozilla/5.0",
        "x-requested-with": "XMLHttpRequest"
    }
    data = {
        "p_xn": xueNian,
        "p_xq": xueQi,
        "p_xnxq": xueNianXueQi,
        "p_chaxunpylx": 3,
        "mxpylx": 3,
        "p_sfhltsxx": 0,
        "pageNum": 1,
        "pageSize": 2000}
    req = requests.post('https://tis.sustech.edu.cn/Xsxktz/queryRwxxcxList', data=data, headers=headers)
    return req.text


def submit(route, JSESSIONID, id):
    headers = {
        "cookie": 'route={}; JSESSIONID={};'.format(route, JSESSIONID),
        "user-agent": "Mozilla/5.0",
        "x-requested-with": "XMLHttpRequest"
    }
    data = {
        "p_pylx": 1,
        "p_xktjz": "rwtjzyx",  # 提交至，可选任务，rwtjzgwc提交至购物车，rwtjzyx提交至已选 gwctjzyx购物车提交至已选
        "p_xn": xueNian,
        "p_xq": xueQi,
        "p_xnxq": xueNianXueQi,
        "p_xkfsdm": "bxxk",  # 补选选课
        "p_id": id,  # 课程id
        "p_sfxsgwckb": 1,  # 固定
    }
    req = requests.post('https://tis.sustech.edu.cn/Xsxk/addGouwuche', data=data, headers=headers)
    if "成功" in req.text:
        print("[\x1b[0;34m{}\x1b[0m]".format("=" * 50))
    print(req.text)


if __name__ == '__main__':
    token = requests.session()
    # 获取要抢的课程
    cachePath = "Class.txt"
    classList = []
    if path.exists(cachePath) and path.isfile(cachePath):
        print("[\x1b[0;36m!\x1b[0m] " + "读取规划课表...")
        with open(cachePath, "r", encoding="utf8") as f:
            classList = f.readlines()
        print("[\x1b[0;32m+\x1b[0m] " + "规划课表读取完毕")
    else:
        print("[\x1b[0;33m-\x1b[0m] " + "没有找到规划课表，请手动输入课程信息，输入-1结束录入")
        while True:
            s = input()
            if s == "-1":
                break
            else:
                classList.append(s)
        s = input("是否保存录入的信息（Y/N）？")
        if s == "Y" or s == "y":
            with open(cachePath, "w", encoding="utf8") as f:
                f.write("===本文件是待选课程的列表，一行输入一个课程名字==请勿删除本行===\n")
                for i in classList:
                    f.write(i + "\n")
                f.close()
    # CAS登录
    route, JSESSIONID = "", ""
    while route == "" or JSESSIONID == "":
        userName = input("请输入您的学号：")
        passWord = input("请输入CAS密码（密码不显示，输入完按回车即可）：")
        route, JSESSIONID = caslogin(token, userName, passWord)
        if route == "" or JSESSIONID == "":
            print("请重试...")
    # 获取课程信息
    classData = {}
    print("[\x1b[0;36m!\x1b[0m] " + "从服务器下载课程信息...")
    rawClassData = loads(getinfo(route, JSESSIONID))
    for i in rawClassData['rwList']['list']:
        classData[i['rwmc']] = i['id']
    print("[\x1b[0;32m+\x1b[0m] " + "课程信息读取完毕")
    print("[\x1b[0;34m{}\x1b[0m]".format("=" * 25))
    # 准备要抢的课程
    postList = []
    for name in classList:
        name = name.strip()
        if name in classData.keys():
            postList.append(classData[name])
            print(name)
    print("[\x1b[0;34m{}\x1b[0m]".format("=" * 25))
    print("[\x1b[0;32m+\x1b[0m] " + "成功读入以上信息")
    # 抢课主逻辑
    while True:
        print("[\x1b[0;32m+\x1b[0m] " + "按一下回车抢三次，多按同时抢多次")
        input()
        for id in postList:
            try:
                _thread.start_new_thread(submit, (route, JSESSIONID, id))
                _thread.start_new_thread(submit, (route, JSESSIONID, id))
                _thread.start_new_thread(submit, (route, JSESSIONID, id))
            except:
                print("线程异常")
