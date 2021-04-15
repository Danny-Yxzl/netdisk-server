# 此处是初始化

import os  # 操作文件和目录不说了
import random  # 分享码生成等
import re
import shutil  # 删除文件夹
import time  # 日志要用
import urllib

import icecream
from flask import *  # 程序的灵魂
from flask_limiter import Limiter  # IP限制
from flask_limiter.util import get_remote_address
from flask_cors import cross_origin, CORS
import requests
import zipfile
import zmail  # 发送邮件
from icecream import ic

import textChecker

thisDir = os.path.dirname(__file__)  # 相对目录
isServer: bool = os.path.isfile(thisDir + "/webserver")
fileDir = "files"  # if isServer else "static/files"
adminList = ["异想之旅"]  # list中的用户可以使用../提权访问所有用户的文件信息
refuseNames = [["temp", "test"], ["yxzl", "异想之旅", "yixiangzhilv"]]
app = Flask(__name__)  # 初始化app对象
app.secret_key = "yxzlpan"  # session的加密密钥
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["17 per 2 second"],  # 默认限制：每2秒请求3次
    default_limits_exempt_when=lambda: (get_remote_address() in adminList)
)
checkText: bool = True  # 是否检查字符串违规信息
ipAreaRecord = {}
domainList = [".yixiangzhilv.com", ".yixiangzhilv.top", ".yxzl.top", "127.0.0.1"]
userMaxSize = {}


# 此处是初始化


# 此处是工具函数定义


def zipDir(dirpath, outFullName):
    zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
    for path, dirNames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, "")
        for filename in filenames:
            zip.write(os.path.join(path, filename),
                      os.path.join(fpath, filename))
    zip.close()


def folder_name_format(folder_name) -> str:
    # 将文件夹格式改为 "a/b/" 或 "" ： 这样在使用时可以最小化改动template，同时统一格式易于管理
    if not folder_name:
        return ""
    if folder_name[-1] != "/":
        folder_name = folder_name + "/"
    if folder_name != "/":
        while "//" in folder_name:
            folder_name = folder_name.replace("//", "/")
        while folder_name[0] == "/":
            folder_name = folder_name[1:]
            if not len(folder_name):
                return ""
        return folder_name
    else:
        return ""


def get_up_folder(folder_name):
    # 获取上级目录
    folder_name = folder_name_format(folder_name)
    folder_name = folder_name.split("/")
    if len(folder_name) > 1:
        del (folder_name[-1])
        folder_name = "/".join(folder_name) + "/"
        return folder_name
    else:
        return ""


def generate_random_str(random_length=16):
    # 生成一个长度为random_length的随机字符串
    random_str = ""
    for i in range(random_length):
        random_str += random.choice("ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789")
    return random_str


def check_session(name):
    # 如果有名为name的session信息就获取、删除并返回内容，用于展示页面通知、分享页分享码等
    if session.get(name):
        value = session.get(name)
        session.pop(name)
    else:
        value = ""
    return value


def encrypt_string(text):
    ans = ""
    for i in text:
        ans = ans + "%s-" % (ord(i) + 99)
    return ans[:-1]


def decode_string(text):
    if text == "iamadmin":
        return text
    # 一个垃圾的字符串解密
    text = text.split("-")
    ans = ""
    for i in text:
        ans = ans + chr(int(i) - 99)
    return ans


def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def get_ip_area(ip):
    if not ip:
        return None
    if ipAreaRecord.get(ip):
        return ipAreaRecord.get(ip)
    result = requests.post(url='http://whois.pconline.com.cn/ipJson.jsp',
                           data={
                               'json': 'true',
                               'ip': ip
                           }).json()['addr']
    ipAreaRecord[ip] = result
    return ipAreaRecord.get(ip)


def logs(username=None, ip=None, event=None):
    # 写入日志信息到文件，并返回本条日志信息；传参具体情况请见调用
    ip = "%s %s" % (ip, get_ip_area(ip))
    text = "%s  %s(%s)%s" % (time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()), username, ip, event)
    f = open("%s/logs/%s.ini" % (thisDir, time.strftime("%Y-%m-%d", time.localtime())),
             "a",
             encoding="UTF-8")
    f.write(text + "\n")
    f.close()
    return text


def email_checker(ip, email, username, password, check=None, host=None) -> bool:
    # 发送验证电子邮件
    print(check)
    try:
        if not ip:
            ip = "未知"
        ip_area = get_ip_area(ip)
        url = "http://%s/set-user/%s/%s/%s?check=%s" % (
            host or request.host, email, username, password, check or encrypt_string(username))
        mail_content = {
            "subject":
                "异想之旅轻量网盘服务邮件验证码",
            "content_html":
                """
                <p>用户你好，有人（IP：%s  参考归属地：%s）正在使用该邮箱地址注册异想之旅轻量网盘服务账号。</p>
                <p>如果确认是你本人所为，请<a href="%s">点我确认</a></p>
                <br />
                <p>该邮件由机器人自动发送，回复邮件或寻求帮助请联系<a href="mailto:mail@yixiangzhilv.com">mail@yixiangzhilv.com</a></p>
                """ % (ip, ip_area, url),
            "from":
                "异想之旅邮箱验证验证 <coder@yixiangzhilv.com>"
        }
        server = zmail.server("coder@yixiangzhilv.com", "@Codercoder")
        server.send_mail([email], mail_content)
        return True
    except:
        return False


def password_checking(a, b) -> bool:
    # 检查两个字符串是否完全相同（我也不知道为甚==不好用了）
    if len(a) != len(b):
        return False
    for i in range(len(a)):
        if a[i] != b[i]:
            return False
    return True


def set_path(new_path):
    # 如果路径不存在则新建文件夹
    if not os.path.isdir(new_path):
        os.makedirs(new_path)


def format_size(size: float, dot=1):
    size = int(size)
    if 0 <= size < 1:
        return str(round(size / 0.125, dot)) + " b"
    elif size < 1024:
        return str(round(size, dot)) + " B"
    elif size < 1048576:
        return str(round(size / 1024, dot)) + " KB"
    elif size < 1073741824:
        return str(round(size / 1048576, dot)) + " MB"
    else:
        return str(round(size / 1073741824, dot)) + " GB"


def get_dir_size(dir_path, formatText=True):
    if not os.path.isdir(dir_path):
        dir_path = "%s/files/%s" % (thisDir, dir_path)
    size = 0
    for root, dirs, files in os.walk(dir_path):
        size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
    if formatText:
        return format_size(size)
    else:
        return size


def get_file_size(filepath):
    # 获取文件大小并直接格式化返回
    size = float(os.path.getsize(filepath))
    return format_size(size)


def get_all_folder_files(folder_path, list_all=False, from_path="") -> list:
    # 遍历目录的所有文件和所有子文件夹中的所有文件并返回list
    # 参数说明：folder_path为文件目录，list_all表示检测到文件夹是否要递归，from_path是本级相对目录便于程序定位文件
    result = []
    get_dir = os.listdir(folder_path)
    for i in get_dir:
        sub_dir = os.path.join(folder_path, i)
        if os.path.isdir(sub_dir):
            # 有子文件夹则递归查找
            # result = result + get_all_folder_files(sub_dir)
            if list_all:
                result = result + get_all_folder_files(sub_dir, list_all, from_path + i + "/")
            else:
                result = result + [[i + "/", "Folder", get_dir_size(sub_dir), from_path]]
        else:
            result = result + [[i,
                                "." + i.split(".")[-1],
                                get_file_size(folder_name_format(folder_path) + i),
                                from_path]]
    return result


def get_user_max_size(username):
    global userMaxSize
    if userMaxSize.get(username):
        return userMaxSize[username]
    try:
        with open("%s/users/%s.password" % (thisDir, username), "r", encoding="utf-8") as f:
            num = int(re.search(".*?\n([\d]*)?\n.*?", f.read()).group(1)) * 1073741824
            userMaxSize[username] = (format_size(num), num)
            return userMaxSize[username]
    except FileNotFoundError:
        return "1.0 GB", 1073741824


def is_number(s, try_type="int"):
    try:
        eval("%s(\"%s\")" % (try_type, s))
        return True
    except ValueError:
        return False


# 此处是工具函数定义


def user_email_check(email, username, password=None):
    with open("%s/sign_up_record.ini" % thisDir, "r", encoding="utf-8") as f:
        text = f.readline()
        while text:
            if "\t%s\t" % email in text and "\t%s\t" % username in text:
                return True
            text = f.readline()
    return False


def info_init():
    session["ip"] = request.headers.get("X-real-ip") or request.remote_addr
    if session.get("username"):
        ...
    elif request.cookies.get("username"):
        session["username"] = decode_string(request.cookies["username"])
    else:
        session["username"] = session.get("ip")
    set_path("%s/%s/%s/" % (thisDir, fileDir, session.get("username")))


# 此处是页面定义


@app.route("/collect/<code>", methods=["GET", "POST"])
def file_collect(code):
    info_init()
    with open("%s/collects/%s.ini" % (thisDir, code), "r", encoding="UTF-8") as f:
        text = f.read().split("\t")
    if request.method == "POST":
        f = request.files["file"]
        if str(f.filename).count(".") == 0:
            flash("上传文件错误：文件必须包含扩展名！")
            return redirect("/collect/%s" % code)
        elif "#" in f.filename:
            flash("上传文件错误：文件名不能包含#！")
            return redirect("/collect/%s" % code)
        set_path("%s/%s/%s/文件收集/%s" % (thisDir, fileDir, text[0], text[1]))
        upload_path = "%s/%s/%s/文件收集/%s/%s" % (thisDir, fileDir, text[0],
                                               text[1], f.filename)
        f.save(upload_path)
        flash("上传文件“%s”成功！" % f.filename)
        print(logs(session.get("username"), session.get("ip"),
                   "上传了文件“%s”到“%s”创建的文件收集任务“%s”" % (f.filename, text[0], text[1])))
        f.close()
        return redirect("/collect/%s" % code)
    else:
        print(logs(session.get("username"), session.get("ip"),
                   "访问了“%s”创建的文件收集任务“%s”" % (text[0], text[1])))
        return render_template("file-collect.html",
                               username=session.get("username"),
                               send_to=text[0],
                               taskname=text[1],
                               is_server=isServer)


@app.route("/set-collect-task", methods=["GET", "POST"])
def set_collect_task():
    if request.method == "GET":
        return redirect("/")
    if session.get("username") == session.get("ip"):
        flash("创建失败：若要使用文件收集功能请先登录！")
        return redirect("/set-collect-task")
    if any(True if i in request.form["taskname"] else False for i in "\\/?:*\"<>|.#"):
        flash("创建失败：任务名称包含非法字符！")
        return redirect("/set-collect-task")
    dir_path = "%s/collects/%s.ini"
    random_code = generate_random_str()
    while os.path.isfile(dir_path % (thisDir, random_code)):
        random_code = generate_random_str()
    set_path("%s/%s/%s/文件收集/%s" % (thisDir,
                                   fileDir,
                                   session.get("username"),
                                   request.form.get("taskname")))
    with open(dir_path % (thisDir, random_code), "w", encoding="UTF-8") as f:
        f.write("%s\t%s" % (session.get("username"), request.form.get("taskname")))
    print(logs(session.get("username"), session.get("ip"),
               "创建了文件收集任务“%s”" % request.form.get("taskname")))
    return redirect("/collect/%s" % random_code)


@app.route("/share/<secret_key>", methods=["GET", "POST"])
@app.route("/shares/<secret_key>", methods=["GET", "POST"])
def share_page(secret_key):
    # 文件分享界面：有传入密钥打开这个分享，否则重定向到通过分享码获取文件
    if not secret_key:
        return redirect("/s")

    info_init()
    try:
        with open("%s/shares/%s.share" % (thisDir, secret_key)) as f:
            text = f.read()
    except FileNotFoundError:
        abort(404)
    shared_by = text[:text.index("/")]
    file_details = text[text.index("/") + 1: text.index("*")].split("?")
    from_path = text[text.index("*") + 1:text.index("|")] \
        if text[::-1].index("*") else ""
    share_code = text[text.index("|") + 1: text.index(":")]
    shared_time = text[text.index(":") + 1:]
    # print(from_path)
    print(
        logs(session.get("username"), session.get("ip"),
             "访问了分享页 \"%s/%s\" 。" % (shared_by, file_details)))

    # 检查文件是否存在，返回分享页面模板或错误提示信息
    if os.path.isfile("%s/%s/%s/%s" % (thisDir, fileDir, shared_by, file_details[0])):
        # 如果是文件（包括多个文件的情况）
        try:  # 仅仅确认了第一个存在，后面的文件可能已被删除
            for i in range(len(file_details)):
                # 确认一下文件名是格式化的（事实上自从前端传参路径格式统一之后这里就不重要了）
                file_details[i] = folder_name_format(file_details[i])[:-1]
                # 为了与get_all_folder_files()的返回值格式匹配，需要加入空项
                file_details[i] = (file_details[i][len(from_path):],
                                   "",  # 函数中会返回文件类型(.*)
                                   get_file_size("%s/%s/%s/%s" % (thisDir,
                                                                  fileDir,
                                                                  shared_by,
                                                                  file_details[i])),
                                   ""  # 函数中返回文件相对路径地址
                                   )
            ic(share_code)
            return render_template("share.html",
                                   shared_by=shared_by,
                                   shared_by_check=encrypt_string(shared_by),
                                   username=session.get("username"),
                                   file_details=file_details,
                                   sharecode=share_code,
                                   show_sharecode=check_session("share-code"),
                                   from_folder="",
                                   is_folder=False,
                                   from_path=from_path,
                                   shared_time=shared_time)
        except FileNotFoundError:
            flash("获取分享文件错误：文件已被删除！")
            return redirect("/s")
    elif os.path.isdir("%s/%s/%s/%s" % (thisDir, fileDir, shared_by, file_details[0])):
        # 是文件夹
        if not request.args.get("path"):
            # 如果没有指定path参数
            from_folder = file_details[0]
        else:
            # 指定了path参数
            from_folder = file_details[0] + request.args.get("path")
            # file_details[0]是标准格式所以不需要额外处理
        try:
            # 获取文件目录下的文件，关闭递归，遇到文件夹返回文件夹名称
            file_details = get_all_folder_files("%s/%s/%s/%s"
                                                % (thisDir, fileDir, shared_by, from_folder))
        except FileNotFoundError:
            flash("文件访问出错：你所访问的路径不存在于该被分享的文件夹中！")
            from_folder = file_details[0]
            file_details = get_all_folder_files("%s/%s/%s/%s"
                                                % (thisDir, fileDir, shared_by, from_folder))
        icecream.ic(from_folder, from_path)
        return render_template("share.html",
                               shared_by=shared_by,
                               shared_by_check=encrypt_string(shared_by),
                               username=session.get("username"),
                               file_details=file_details,
                               sharecode=share_code,
                               show_sharecode=check_session("share-code"),
                               from_folder=folder_name_format(from_folder)[max(len(from_path) - 1, 0):],
                               is_folder=True,
                               from_path=from_path,
                               shared_time=shared_time)
    else:
        # 不是文件也不是文件夹的情况
        flash("获取分享文件错误：文件已被发布者删除！")
        return redirect("/s")


@app.route("/get-share-file-by-code", methods=["GET", "POST"])
@app.route("/s", methods=["GET", "POST"])
@app.route("/get-share", methods=["GET", "POST"])
def get_share_file_by_code():
    # 通过分享码获取链接
    if request.method == "POST":
        print(
            logs(session.get("username"), session.get("ip"),
                 "通过分享码 \"%s\" 获取了分享链接。" % (request.form["share-code"])))
        if os.path.isfile("%s/shares/%s.sharecode" % (thisDir, request.form["share-code"])):
            with open("%s/shares/%s.sharecode" % (thisDir, request.form["share-code"]), "r") as f:
                return redirect("/share/%s" % (f.read()))
        else:
            flash("通过分享码获取分享文件时出错：找不到分享码“%s”对应的文件！" % request.form["share-code"])
            return redirect("/s")
    else:
        return render_template("get_share_file_by_code.html",
                               username=session.get("username"))


@app.route("/get-shares-url/<username>", methods=["POST"])
def get_shares_url(username):
    # 复选框选中多个文件分享
    if request.values.to_dict()["data"] == "":
        return "../"
    files_name = request.values.to_dict()["data"][1:].split(",|")
    share_code = str(random.randint(1000, 9999))
    secret_key = "%s/%s*%s|%s:%s" % (username, "?".join(files_name),
                                     request.args.get("path") or "", share_code,
                                     int(time.time()))
    url = generate_random_str()
    with open("%s/shares/%s.sharecode" % (thisDir, share_code), "w") as f:
        f.write(url)
    with open("%s/shares/%s.share" % (thisDir, url), "w") as f:
        f.write(secret_key)
    print(
        logs(session.get("username"), session.get("ip"),
             "计算了分享链接 \"%s\" （分享码为%s）。" % (url, share_code)))
    session["share-code"] = share_code
    return "/share/" + url


@app.route("/get-share-url/<username>/<path:filepath>", methods=["POST"])
def get_share_url(username, filepath):
    # 分享单个文件或文件夹：两者在此步骤操作相同，都是生成分享链接后保存被分享文件路径
    filepath = filepath.replace("//", "/")
    if checkText and random.random() > 0.9:
        text_check_result = textChecker.check(filepath)
        if text_check_result != "normal":
            flash("文件分享失败：文件名审核不通过！（参考信息 %s）" % text_check_result)
            return redirect("/s")
    # 打印日志，获取该文件的分享链接（加密）并重定向
    share_code = str(random.randint(1000, 9999))
    secret_key = "%s/%s*%s|%s:%s" % (username, filepath, request.args.get("path") or "",
                                     share_code, int(time.time()))
    url = generate_random_str()
    with open("%s/shares/%s.sharecode" % (thisDir, share_code), "w") as f:
        f.write(url)
    with open("%s/shares/%s.share" % (thisDir, url), "w") as f:
        f.write(secret_key)
    print(
        logs(session.get("username"), session.get("ip"),
             "计算了分享链接 \"%s\" （分享码为%s）。" % (filepath, share_code)))
    session["share-code"] = share_code
    return redirect("/share/%s" % url)


@app.route("/rename/<username>/<path:old_name>", methods=["POST"])
def rename(username, old_name):
    if "#" in request.form["new_name"]:
        flash("重命名失败：文件名不支持包含#！")
        return redirect("/?path=%s" % (request.args.get("path") if request.args.get("path") else ""))
    if "../" in request.form["new_name"] or "..\\" in request.form["new_name"]:
        flash("新建目录失败：同志，请别尝试通过 ../  的方式修改服务器目录！")
        return redirect("/?path=%s" % request.args.get("path"))
    # 根据传参计算文件具体路径后利用os库重命名文件并刷新当前页
    new_name = (folder_name_format(request.args.get("path")) if request.args.get("path") else "") + request.form[
        "new_name"]
    old_name = "%s/%s/%s/%s/%s" % (thisDir, fileDir, username,
                                   request.args.get("path"), old_name)
    if not new_name.endswith(old_name.split(".")[-1]) and os.path.isfile(old_name):
        new_name = new_name + "." + old_name.split(".")[-1]
        print(
            logs(session.get("username"), session.get("ip"),
                 "重命名了文件 \"%s\" -> \"%s\" 。" % (old_name, new_name + " （自动补全扩展名）")))
    else:
        print(
            logs(session.get("username"), session.get("ip"),
                 "重命名了文件 \"%s\" -> \"%s\" 。" % (old_name, new_name)))
    new_name = "%s/%s/%s/%s" % (thisDir, fileDir, username, new_name)
    try:
        os.rename(old_name, new_name)
        if "{{" in new_name and "}}" in new_name:
            # 如果有Jinja2语法出现则可能是SSTI攻击
            flash("同志，你的行为疑似SSTI攻击，我已经通知我父亲好好关照你了！")
    except FileExistsError:
        flash("重命名出错：文件\"%s\"已存在，无法保存两个同名文件！" % request.form["new_name"])
    except OSError:
        # 有了这个try语句可以省去一堆复杂的文件名合法性检测
        flash("重命名出错：文件名中存在非法字符！")
    return redirect("/?path=%s" %
                    (folder_name_format(request.args.get("path"))
                     if request.args.get("path") else ""))


@app.route("/deletes", methods=["POST", "DELETE"])
@limiter.limit("1 per 2 seconds")
def deletes():
    files = request.values.to_dict()["data"][1:].split(",|")
    filepath = "%s/%s/%s/" % (thisDir,
                              fileDir,
                              session.get("username"))
    print(
        logs(session.get("username"), session.get("ip"),
             "删除了文件 \"%s\" 。" % files))
    for i in files:
        try:
            os.remove(filepath + i)
        except FileNotFoundError:
            flash("删除失败：没有找到文件\"%s\"！" % filepath)
    return "/?path=" + folder_name_format(request.args.get("path"))


@app.route("/delete/<username>/<path:filepath>", methods=["POST", "DELETE"])
@limiter.limit("3 per 2 seconds")
def delete(username, filepath):
    filepath = request.args.get("path") + filepath
    # 打印日志，根据传参计算文件具体路径，删除文件
    print(
        logs(session.get("username"), session.get("ip"),
             "删除了文件 \"%s\" 。" % filepath))
    filepath = "%s/%s/%s/%s" % (thisDir, fileDir, username, filepath.replace("%2F", "/"))
    filepath = filepath.replace("//", "/").replace("//", "/")
    if os.path.isdir(filepath):
        try:
            shutil.rmtree(filepath)
        except FileNotFoundError:
            flash("删除失败：没有找到文件夹\"%s\"！" % filepath)
    else:
        try:
            os.remove(filepath)
        except FileNotFoundError:
            flash("删除失败：没有找到文件\"%s\"！" % filepath)
    return redirect("/?path=%s" % folder_name_format(request.args.get("path")))


@app.route("/set-dir/<username>", methods=["POST"])
def set_dir(username):
    # 新建文件夹操作
    new_name = request.form.get("new_folder_name")
    print(
        logs(session.get("username"), session.get("ip"),
             "新建了文件夹 \"%s\" 。" % new_name))
    if "../" in new_name or "..\\" in new_name:
        flash("新建目录失败：同志，请别尝试通过 ../ 或 ..\\ 的方式修改服务器目录！")
        return redirect("/?path=%s" % (request.args.get("path")))
    elif "+" in new_name:
        flash("新建目录失败：由于会引发无法定位的错误，暂时不接受带有“+”的文件夹名称！")
        return redirect("/?path=%s" % (request.args.get("path")))
    dirpath = "%s/%s/%s/%s/%s" % (thisDir,
                                  fileDir,
                                  username,
                                  request.args.get("path"),
                                  new_name)
    try:
        set_path(dirpath)
        if "{{" in new_name and "}}" in new_name:
            flash("同志，你的行为疑似SSTI攻击，我已经通知我父亲好好关照你了！")
    except NotADirectoryError:
        flash("新建目录失败：目录名称无效。")
    except OSError:
        flash("新建目录失败：文件夹名称非法。")
    finally:
        return redirect("/?path=%s" % folder_name_format(request.args.get("path")))


def send_chunk(filepath):
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(20971520)  # 每次读取20M
            if not chunk:
                break
            yield chunk


@app.route("/download/<from_user>/<path:filename>")
def download_file(from_user, filename):
    info_init()
    filename = urllib.parse.unquote(filename)
    from_user = urllib.parse.unquote(from_user)
    if from_user == session.get("username") or \
            (request.args.get("check") and
             (from_user == decode_string(request.args.get("check"))
              or request.args.get("check") == "iamadmin")):
        filepath = "%s/%s/%s/%s" % (thisDir, fileDir, from_user, filename)
        if os.path.isdir(filepath):
            if get_dir_size(filepath, formatText=False) >= 536870912:
                filepath = "%s/temp/error.zip" % thisDir
                return Response(send_chunk(filepath),
                                content_type="application/octet-stream")
            zipDir(filepath, "%s/temp/zip/%s-%s.zip" % (thisDir, from_user,
                                                        filename.replace("/", "-")))
            filepath = "%s/temp/zip/%s-%s.zip" % (thisDir, from_user,
                                                  filename.replace("/", "-"))
        print(
            logs(session.get("username"), session.get("ip"),
                 "下载了文件 \"%s/%s\" 。" % (from_user, filename)))
        return Response(send_chunk(filepath), content_type="application/octet-stream")
    else:
        return abort(404)


@app.route("/upload", methods=["POST"])
def upload_file():
    f = request.files["file"]
    if get_dir_size(session["username"], False) >= get_user_max_size(session["username"])[1]:
        flash("上传失败：年轻人，你以为文件上传也只是一个前端限制吗？")
        return redirect("/?path=%s" % folder_name_format(request.args.get("path")))
    if str(f.filename).count(".") == 0:
        flash("上传文件错误：文件必须包含扩展名！")
        return redirect("/?path=%s" % folder_name_format(request.args.get("path")))
    elif "#" in f.filename:
        flash("上传文件错误：文件名不能包含#！")
        return redirect("/?path=%s" % folder_name_format(request.args.get("path")))
    try:  # 我也不知道会不会出错哪里会出错反正加个try总没错
        folder_name = session.get("username")
        folder_name = folder_name + ("/" + folder_name_format(request.args.get("path")))
        set_path("%s/%s/%s/" % (thisDir, fileDir, folder_name))
        upload_path = "%s/%s/%s/%s" % (thisDir, fileDir, folder_name, f.filename)
        f.save(upload_path)
        print(
            logs(session.get("username"), session.get("ip"),
                 "上传了文件 \"%s%s\" 。" % (folder_name, f.filename)))
        f.close()
    except:
        print(
            logs(session.get("username"), session.get("ip"),
                 "上传文件 \"%s\" 时出现错误！" % folder_name))
    finally:
        return redirect("/?path=%s" % folder_name_format(request.args.get("path")))


@app.route("/", methods=["GET"])
def index():
    # 首页需要确认用户名和IP，方便模板传参和日志处理
    info_init()
    files = "%s/%s/%s/" % (thisDir, fileDir, session.get("username"))
    if request.args.get("path"):
        files = files + folder_name_format(request.args.get("path"))
    if os.path.isdir(files):
        files = get_all_folder_files(files)
    elif os.path.isdir(files.replace(" ", "+")):
        files = get_all_folder_files(files.replace(" ", "+"))
    else:
        flash("访问失败：同志，你的网盘中没有这个目录！")
        return redirect("/")

    if session["username"] not in adminList \
            and ".." in folder_name_format(request.args.get("path")):
        flash("访问失败：年轻人，访问路径中加入../尝试提权访问可是个危险的行为哦！")
        return redirect("/?path=")
    if request.args.get("path") and "{{" in request.args.get("path") and "}}" in request.args.get("path"):
        flash("同志，你的行为疑似SSTI攻击，我已经通知我父亲好好关照你了！")

    print(logs(session.get("username"), session.get("ip"), "访问了首页。"))
    return render_template("index.html",
                           url=request.url_root[:-1],
                           files=files,
                           folder=folder_name_format(request.args.get("path")),
                           up_folder=get_up_folder(request.args.get("path")),
                           sum_size=(get_dir_size(session.get("username")),
                                     get_dir_size(session.get("username"),
                                                  formatText=False)),
                           max_size=get_user_max_size(session.get("username")))


@app.route("/login", methods=["POST", "GET"])
def login():
    # todo 回到登录前访问的界面
    if request.method == "POST":
        if any(request.form["username"].startswith(i) for i in refuseNames[0]) \
                and (not request.form["username"][4:]
                     or is_number(request.form["username"][4:])):
            session["username"] = request.form["username"]
            return redirect("/")
        # POST是登录检查请求
        password_filename = "%s/users/%s.password" % (
            thisDir, request.form["username"])
        if os.path.isfile(password_filename):  # 如果存在有用户名对应的密码文件
            f = open(password_filename, "r", encoding="UTF-8")
            password = f.readline()[:-1]
            if password_checking(request.form["password"], password):
                # 匹配通过则登录成功，session获取username，打印日志，返回首页
                session["username"] = request.form["username"]
                f.close()
                resp = make_response(redirect(request.args.get("from") or "/"))
                domain = re.search("https?://(.*)?:?([\d]*)?/.*",
                                   request.url).group(1)
                resp.set_cookie(key="username",
                                value=encrypt_string(session.get("username")),
                                max_age=86400 * 365,
                                domain=domain[domain.index("."):])
                print(
                    logs(session.get("username"), session.get("ip"),
                         "成功登录（密码为\"%s\"）。" % (request.form["password"])))
                return resp
            else:
                # 比对不通过，返回提示信息
                f.close()
                flash("登录失败：用户名和密码不匹配，请检查输入！")
                return redirect("/login?from=%s" % request.args.get("from") or "")
        else:
            # 不存在用户名对应的密码文件，即无此用户，重新加载并显示通知
            flash("登录失败：没有找到用户\"%s\"！" % request.form["username"])
            return redirect("/login?from=%s" % request.args.get("from") or "")
    else:
        # GET是获取登录页，打印日志并返回登录页
        print(logs(session.get("username"), session.get("ip"), "访问了登录界面。"))
        return render_template("login.html", login_page=True,
                               from_url=request.args.get("from"))


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    info_init()
    if request.method == "POST":
        # 重置密码部分
        if request.form["username"] == session.get("username"):  # 修改当前登录的账号的密码
            f = open("%s/sign_up_record.ini" % thisDir, "a", encoding="UTF-8")
            f.write("%s\t%s\t%s\t%s\t%s\n" % (time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime()), request.form["email"],
                                              request.form["username"],
                                              request.form["password"], session.get("ip")))
            f.close()
            f = open("%s/users/%s.password" % (thisDir, request.form["username"]), "r", encoding="utf-8")
            text = f.read()
            print([text])
            text = text[text.index("\n"):]
            f.close()
            f = open("%s/users/%s.password" % (thisDir, request.form["username"]), "w", encoding="utf-8")
            f.write(request.form["password"] + text)
            f.close()
            flash("修改密码成功！")
            return redirect("/")
        elif user_email_check(request.form["email"], request.form["username"]):
            # 修改未登录的账号的密码
            random.seed(request.form["username"])
            if email_checker(ip=session.get("ip"),
                             email=request.form["email"],
                             username=request.form["username"],
                             check=encrypt_string("%s?%s" % (request.form["username"],
                                                             random.randint(100000,
                                                                            999999))),
                             password=request.form["password"]):
                print(
                    logs(session.get("username"), session.get("ip"),
                         "获取重置密码验证电子邮件成功（%s）。" % request.form["email"]))
                flash("重置密码验证邮件发送成功，请前往邮箱查看并完成修改操作！")
                return redirect("/sign-up")
            else:
                flash("重置密码失败：暂时无法获取验证邮件，请稍后再试。")
                return redirect("/sign-up")

        # 先检查用户名是否合法
        if request.form["username"].count(".") == 3:
            flash("注册失败：用户名疑似IP地址，不予注册！")
            return redirect("/sign-up")
        elif len(request.form["username"]) > 20:
            flash("注册失败：用户名过长。")
            return redirect("/sign-up")
        elif os.path.isfile("%s/users/%s.password" % (thisDir, request.form["username"])):
            flash("注册失败：用户名已存在。")
            return redirect("/sign-up")
        elif any(i in request.form["username"] for i in "\\/?:*\"<>|."):
            flash("注册失败：用户名包含非法字符，Windows不能正确读取！非法字符列表：\\ / ? : * \" < > | .")
            return redirect("/sign-up")
        elif any(request.form["username"].startswith(check) for check in refuseNames[0]) \
                or any(check in request.form["username"] for check in refuseNames[1]):
            flash("注册失败：该用户名是异想之旅保留的字段，不予注册！")
            return redirect("/sign-up")
        elif textChecker.check(request.form.get("username")) != "normal":
            # 这个检测要付费，自然放最后
            flash("注册失败：用户名自动校验不予通过！")
            return redirect("/sign-up")
        if "{{" in request.form["username"] and "}}" in request.form["username"]:
            flash("同志，你的行为疑似SSTI攻击，我已经通知我父亲好好关照你了！")
        if email_checker(ip=session.get("ip"),
                         email=request.form["email"],
                         username=request.form["username"],
                         password=request.form["password"]):
            print(
                logs(session.get("username"), session.get("ip"),
                     "获取验证电子邮件成功（%s）。" % (request.form["email"])))
            flash("验证邮件发送成功，请前往邮箱查看并完成注册！")
            return redirect("/sign-up")
        else:
            flash("注册失败：暂时无法获取验证邮件，请稍后再试。")
            return redirect("/sign-up")
    else:
        print(logs(session.get("username"), session.get("ip"), "访问了注册页。"))
        return render_template("sign_up.html")


@app.route("/set-user/<email>/<username>/<password>", methods=["GET", "POST"])
@limiter.limit("1 per day",
               exempt_when=lambda: (get_remote_address() in adminList),
               error_message="Sorry, an IP address can only set one account in 24 hours.")
def set_user(email, username, password):
    info_init()
    random.seed(username)
    if request.args.get("check") != "iamadmin" \
            and not (password_checking(decode_string(request.args.get("check")),
                                       "%s?%s" % (username, random.randint(100000, 999999)))
                     or password_checking(decode_string(request.args["check"]), username)):
        print(logs(username, session.get("ip"), "：注册时校验码错误"))
        flash("警告：注册校验码错误！请勿尝试刷账号，否则将会封禁IP。")
        return redirect("/sign-up")
    random.seed(username)
    if os.path.isfile(thisDir + "/users/%s.password" % username) and not (
            request.args.get("check") == "iamadmin" or
            password_checking(decode_string(request.args.get("check")),
                              "%s?%s" % (username, random.randint(100000, 999999)))):
        print(logs(username, session.get("ip"), "：该用户名被违规重复注册（密码为\"%s\"）！" % password))
        flash("警告：该用户名已被注册！恶意注册将会封IP处理，请谨慎。")
        return redirect("/sign-up")
    # 写入注册记录
    with open("%s/sign_up_record.ini" % thisDir, "a", encoding="utf-8") as f:
        f.write("%s\t%s\t%s\t%s\t%s\n" % (time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime()), email, username, password, session.get("ip")))
    reset_password = os.path.isfile("%s/users/%s.password" % (thisDir, username))
    if reset_password:
        with open("%s/users/%s.password" % (thisDir, username), "r", encoding="UTF-8") as f:
            text = f.read()
            text = password + text[text.index("\n"):]
    with open("%s/users/%s.password" % (thisDir, username), "w", encoding="UTF-8") as f:
        if reset_password:
            f.write(text)
        else:
            f.write("%s\n5\n" % password)
    print(logs(username, session.get("ip"), "%s成功（密码为\"%s\"）。"
               % ("注册" if decode_string(request.args.get("check")) == username
                  else "修改密码", password)))
    flash("成功%s用户%s。" % (username,
                         "注册" if decode_string(request.args.get("check")) == username else "修改密码"))
    session["username"] = username
    resp = make_response(redirect("/"))
    domain = re.search("https?://(.*)?:?([\d]*)?/.*", request.url).group(1)
    resp.set_cookie(key="username",
                    value=encrypt_string(session.get("username")),
                    max_age=86400 * 365,
                    domain=domain[domain.index("."):])
    set_path("%s/%s/%s/" % (thisDir, fileDir, username))
    return resp


@app.route("/logout")
@limiter.limit("1 per 2 second")
def logout():
    info_init()
    # 清除username信息（重新赋值为IP地址）并重定向至主页
    print(logs(session.get("username"), session.get("ip"), "登出成功。"))
    session["username"] = session.get("ip")
    resp = make_response(redirect("/"))
    domain = re.search("https?://(.*)?:?([\d]*)?/.*", request.url).group(1)
    resp.delete_cookie(key="username",
                       domain=domain[domain.index("."):])
    return resp


@app.route("/404")
@app.errorhandler(404)
def to_index(info=None):
    flash("404：你刚刚访问了不存在的资源，已为你重定向到主页！")
    return redirect("/")


# 此处是页面定义


@app.route("/ip")
def return_ip():
    info_init()
    # return jsonify({'X-Real-IP': request.environ['X-Real-IP'],
    #                 'HTTP_X_FORWARDED_FOR':
    #                     request.environ['HTTP_X_FORWARDED_FOR']}), 200
    return request.host
    # return session.get("ip")


@app.route("/decode-string", methods=["POST"])
@cross_origin()
def return_decode_string():
    if not any((i in request.host) for i in domainList):
        print(request.headers.get("Host"))
        return "跨域错误！"
    text = decode_string(request.values.get("secret") or "")
    return text.title()


@app.context_processor
def default():
    username = session.get("username")
    return dict(username=username, is_server=isServer)


if __name__ == "__main__":
    print(logs(event="服务器启动成功。"))
    app.run(debug=True, port=8000, host="0.0.0.0")
