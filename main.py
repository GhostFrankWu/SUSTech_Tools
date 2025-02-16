#!/usr/bin/env python3    # -*- coding: utf-8 -*

"""
main.py 南科大TIS喵课助手

@CreateDate 2021-1-9
@UpdateDate 2024-9-9
"""

import _thread
import time
import os
from getpass import getpass
from json import loads, dumps
from re import findall
import datetime

import requests
from colorama import init

import sys
import warnings
from urllib3.exceptions import InsecureRequestWarning


def warn(message, category, filename, lineno, _file=None, line=None):
    if category is not InsecureRequestWarning:
        sys.stderr.write(warnings.formatwarning(
            message, category, filename, lineno, line))


CLASS_CACHE_PATH = "class.txt"
COURSE_INFO_PATH = "course.txt"
warnings.showwarning = warn
SUCCESS = "[\x1b[0;32m+\x1b[0m] "
STAR = "[\x1b[0;32m*\x1b[0m] "
ERROR = "[\x1b[0;31mx\x1b[0m] "
INFO = "[\x1b[0;36m!\x1b[0m] "
FAIL = "[\x1b[0;33m-\x1b[0m] "
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
head = {
    "user-agent": UA,
    "x-requested-with": "XMLHttpRequest"
}

COURSE_TYPE = {'bxxk': "通识必修选课", 'xxxk': "通识选修选课", "kzyxk": '培养方案内课程',
               "zynknjxk": '非培养方案内课程', "jhnxk": '计划内选课新生'}

course_list = []  # 需要喵的课程队列
# 由于Tis的新限制，逻辑改为同时只选一门课



UesrID = ""
UserPasswd = ""




def get_endTime(startTime,durationTime):
    # 1. 将字符串时间转换为 datetime.time 对象
    time_obj = datetime.datetime.strptime(startTime, "%H:%M").time()

    # 2. 创建一个 datetime.datetime 对象，使用今天日期和转换后的时间
    today = datetime.date.today()
    start_datetime = datetime.datetime.combine(today, time_obj)

    # 3. 创建一个 timedelta 对象，表示持续时间
    duration_delta = datetime.timedelta(minutes=int(durationTime))

    # 4. 将 timedelta 对象添加到 datetime 对象
    end_datetime = start_datetime + duration_delta

    # 5. 将结果 datetime 对象转换为字符串，格式化为 "HH:MM"
    Time2End = end_datetime.strftime("%H:%M")
    print("结束时间：",Time2End)
    return Time2End

# 设置自动运行时间
Time2Run = "10:35" # 开始时间
Duration = "10" # 单位是分钟
Time2End = get_endTime(Time2Run,Duration)

#超参数
SumbitDelay = 1  # 抢课信息提交间隔时间，单位：秒
MaxThread = 10   # 最大线程数 



def load_course():
    """ 用于加载本地要喵的课程
    如果存在文件就读文件里的，不存在就手动录入
    有些(我忘了是哪些了)情况会在文件头会有几个不可见字符，但是会被python读进来，所以第一行建议忽略留空"""
    courses = []
    if os.path.exists(CLASS_CACHE_PATH) and os.path.isfile(CLASS_CACHE_PATH):
        print(INFO + "读取规划课表...")
        with open(CLASS_CACHE_PATH, "r", encoding="utf8") as f:
            courses = f.readlines()
        print(SUCCESS + "规划课表读取完毕")
    else:
        print(FAIL + "没有找到规划课表，请手动输入课程信息，输入-1结束录入")
        s = "===本文件是待喵课程的列表，一行输入一个课程名字==请勿删除本行==="
        while s != "-1":
            courses.append(s)
            s = input()
        s = input(INFO + "是否保存录入的信息（y/N）？")
        if s in "yY":
            with open(CLASS_CACHE_PATH, "w", encoding="utf8") as f:
                f.writelines('\n'.join(courses))
    return courses


def cas_login(sid, pwd):
    """ 用于和南科大CAS认证交互，拿到tis的有效cookie
    输入用于CAS登录的用户名密码，输出tis需要的全部cookie内容(返回头Set-Cookie段的route和jsessionid)
    我的requests的session不吃CAS重定向给到的cookie，不知道是代码哪里的问题，所以就手动拿了 """
    print(INFO + "测试CAS链接...")
    try:  # Login 服务的CAS链接有时候会变
        login_url = "https://cas.sustech.edu.cn/cas/login?service=https%3A%2F%2Ftis.sustech.edu.cn%2Fcas"
        req = requests.get(login_url, headers=head, verify=False)
        assert (req.status_code == 200)
        print(SUCCESS + "成功连接到CAS...")
    except Exception as ex:
        print(ERROR + f"不能访问CAS, 请检查您的网络连接状态 ({ex})")
        return "", ""
    print(INFO + "登录中...")
    data = {  # execution大概是CAS中前端session id之类的东西
        'username': sid,
        'password': pwd,
        'execution': str(req.text).split('''name="execution" value="''')[1].split('"')[0],
        '_eventId': 'submit',
        'geolocation': ''  # 新字段
    }
    while True:
        req = requests.post(login_url, data=data,
                            allow_redirects=False, headers=head, verify=False)
        if req.status_code == 500:
            print(ERROR + "CAS服务出错，重试中")
        break
    if "Location" in req.headers.keys():
        print(SUCCESS + "登录成功")
    else:
        print(ERROR + "用户名或密码错误，请检查")
        return "", ""
    req = requests.get(
        req.headers["Location"], allow_redirects=False, headers=head, verify=False)
    _route = findall('route=(.+?);', req.headers["Set-Cookie"])[0]
    _jsessionid = findall('JSESSIONID=(.+?);', req.headers["Set-Cookie"])[0]
    return _route, _jsessionid


def getinfo(semester_data):
    """ 用于向tis请求当前学期的课程ID，得到的ID将用于选课的请求
    输入当前学期的日期信息，返回的json包括了课程名和内部的ID """
    if os.path.exists(COURSE_INFO_PATH) and os.path.isfile(COURSE_INFO_PATH):
        print(INFO + f"读取本地缓存的课程信息，如果需要更新请删除{COURSE_INFO_PATH}文件")
        with open(COURSE_INFO_PATH, "r", encoding="utf8") as f:
            cached_course_list = f.readlines()
        try:
            cached_time = cached_course_list[0].strip()
            if cached_time == semester_data['p_xnxq']:
                _course_info = loads(cached_course_list[1])
                print(SUCCESS + f"课程信息读取完毕，共读取{str(len(_course_info))}门课程信息\n")
                return _course_info
            else:
                print(INFO + "缓存文件已过期，重新获取课程信息")
        except Exception as ex:
            print(ERROR + f"缓存文件损坏，重新获取课程信息，{ex}")
    print(INFO + "从服务器下载课程信息，请稍等...")
    _course_info = {}
    for c_type in COURSE_TYPE.keys():
        data = {
            "p_xn": semester_data['p_xn'],  # 当前学年
            "p_xq": semester_data['p_xq'],  # 当前学期
            "p_xnxq": semester_data['p_xnxq'],  # 当前学年学期
            "p_pylx": 1,
            "mxpylx": 1,
            "p_xkfsdm": c_type,
            "pageNum": 1,
            "pageSize": 1000  # 每学期总共开课在1000左右，所以单分类可以包括学期的全部课程
        }
        print("[\x1b[0;36m*\x1b[0m] " + f"获取 {COURSE_TYPE[c_type]} 列表...")
        req = requests.post('https://tis.sustech.edu.cn/Xsxk/queryKxrw',
                            data=data, headers=head, verify=False)
        raw_class_data = loads(req.text)
        if raw_class_data.get('kxrwList'):
            for i in raw_class_data['kxrwList']['list']:
                _course_info[i['rwmc']] = (i['id'], c_type)
    print(SUCCESS + f"课程信息读取完毕，共读取{str(len(_course_info))}门课程信息")
    s = input(INFO + "是否保存读取的课程信息（y/N）？")
    if s in "yY":
        with open(COURSE_INFO_PATH, "w", encoding="utf8") as f:
            f.write(str(semester_data['p_xnxq']) + "\n")
            f.write(dumps(_course_info))
    return _course_info


def submit(semester_data, loop=3):
    """ 用于向tis发送喵课的请求
    这里假设主要耗时在网络IO上，本地处理时间几乎可以忽略
    （什么，购物车是怎么回事？那首先排除教务系统是个魔改的电商项目）"""
    for _ in range(loop):
        if not course_list:
            print(SUCCESS + "⌯'ㅅ'⌯所有课程已喵完，再见😾")
            exec("os._exit(0)")  # lint hack
        c_id, c_type, c_name = course_list[0]
        data = {
            "p_pylx": 1,
            "p_xktjz": "rwtjzyx",  # 提交至，可选任务，rwtjzgwc提交至购物车，rwtjzyx提交至已选 gwctjzyx购物车提交至已选
            "p_xn": semester_data['p_xn'],
            "p_xq": semester_data['p_xq'],
            "p_xnxq": semester_data['p_xnxq'],
            "p_xkfsdm": c_type,  # 选课方式
            "p_id": c_id,  # 课程id
            "p_sfxsgwckb": 1,  # 固定
        }
        req = requests.post('https://tis.sustech.edu.cn/Xsxk/addGouwuche',
                            data=data, headers=head, verify=False)
        res = loads(req.text)['message']
        if "成功" in req.text:
            print("[\x1b[0;34m{}\x1b[0m]".format("=" * 50), flush=True)
            print("[\x1b[0;34m█\x1b[0m]\t\t\t" + res, flush=True)
            print("[\x1b[0;34m{}\x1b[0m]".format("=" * 50), flush=True)
            course_list.pop(0)
        else:
            print("[\x1b[0;30m-\x1b[0m]\t\t\t" + res, flush=True)
        if any(map(lambda x: x in req.text, ["冲突", "已选", "已满"])):
            print(f"[\x1b[0;31m!\x1b[0m] ({c_name})因为({res})跳过", flush=True)
            course_list.pop(0)
        time.sleep(SumbitDelay)


if __name__ == '__main__':
    init(autoreset=True)  # 某窗口系统的优质终端并不直接支持如下转义彩色字符，所以需要一些库来帮忙
    course_name_list = load_course()  # 读取本地待喵的课程
    # 下面是CAS登录
    route, jsessionid = "", ""
    while route == "" or jsessionid == "":
        if UesrID != "":
            user_name = UesrID
            pass_word = UserPasswd
        else:
            user_name = input("请输入您的学号：")  # getpass在PyCharm里不能正常工作，请改为input或写死
            pass_word = getpass("请输入CAS密码（密码不显示，输入完按回车即可）：")
        route, jsessionid = cas_login(user_name, pass_word)
        if route == "" or jsessionid == "":
            print(FAIL + "请重试...")
    head['cookie'] = f'route={route}; JSESSIONID={jsessionid};'
    # 下面先获取当前的学期
    print(INFO + "从服务器获取当前喵课时间...")
    semester_info = loads(
        requests.post('https://tis.sustech.edu.cn/Xsxk/queryXkdqXnxq',
                      # 这里要加mxpylx才能获取到选课所在最新学期
                      data={"mxpylx": 1}, headers=head, verify=False).text)
    print(SUCCESS + f"当前学期是{semester_info['p_xn']}学年第{semester_info['p_xq']}学期，为"
          f"{['', '秋季', '春季', '小'][int(semester_info['p_xq'])]}学期")
    # 然后获取本学期全部课程信息
    print(INFO + "读取课程信息...")
    course_info = getinfo(semester_info)
    # 分析要喵课程的ID
    for name in course_name_list:
        name = name.strip()
        if name in course_info.keys():
            course_id, course_type = course_info[name]
            course_list.append([course_id, course_type, name])
    print("[\x1b[0;34m{}\x1b[0m]".format("=" * 25))
    for course in course_list:
        print(f"{COURSE_TYPE[course[1]]} : {course[2]}\t\tID为: {course[0]}")
    print("[\x1b[0;34m{}\x1b[0m]".format("=" * 25))
    print(SUCCESS + "成功读入以上信息\n")
    # 喵课主逻辑
    CurrentThreadNum = 0
    while True:
        if not course_list:
            print(SUCCESS + "⌯'ㅅ'⌯所有课程已喵完，再见😾")
            exec("os._exit(0)")  # lint hack
        while course_list:
            current_time = datetime.datetime.now().strftime("%H:%M")
            if current_time > Time2Run and current_time < Time2End:
                if CurrentThreadNum >=  MaxThread:
                    exec("os._exit(0)")  # lint hack
                try:
                    _thread.start_new_thread(submit, (semester_info, 3))
                    CurrentThreadNum += 1
                except Exception as e:
                    print(f"[{e}] 线程异常")
                time.sleep(1)

"""
# timing is everything!
    import datetime,time
import datetime
    start = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '12:55', '%Y-%m-%d%H:%M')
    end = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '13:05', '%Y-%m-%d%H:%M')
    while True:
        n_time = datetime.datetime.now()
        if start < n_time < end:
            for c_id in postList:
                try:
                    submit(semester_info, c_id)
                except:
                    pass
            time.sleep(0xdeadbeef)
        time.sleep(0xc0febabe)
"""
