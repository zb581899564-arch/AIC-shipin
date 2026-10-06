# -*- coding: utf-8 -*-
"""抓取百度网盘分享页的文件清单，验证是否为 QVHighlights 公开数据集。

用法: python3 bd_share_ls.py <分享链接> <提取码>
无需登录账号，仅用"分享页验证接口 + 分享列表接口"。
"""
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

share_url = sys.argv[1]
pwd = sys.argv[2]

# 解析 surl（去掉开头 "1" 前缀）
m = re.search(r"/s/1([A-Za-z0-9_-]+)", share_url)
surl = m.group(1)

cookies = {}
referer = "https://pan.baidu.com/s/1" + surl


def http_get(url, extra_cookie=None):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Referer": referer,
    })
    cookie_str = "; ".join("%s=%s" % kv for kv in cookies.items())
    if extra_cookie:
        cookie_str = (cookie_str + "; " + extra_cookie) if cookie_str else extra_cookie
    if cookie_str:
        req.add_header("Cookie", cookie_str)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")


def http_post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                 headers={"User-Agent": UA, "Referer": referer,
                                          "X-Requested-With": "XMLHttpRequest"})
    cookie_str = "; ".join("%s=%s" % kv for kv in cookies.items())
    if cookie_str:
        req.add_header("Cookie", cookie_str)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")


def set_cookies_from_headers():
    import http.cookiejar
    return


# 第一步：请求分享页拿初始 cookie (BAIDUID 等)
html = http_get(share_url)
# urllib 不自动存 cookie，手动从 curl cookie jar 处理太麻烦，改用 curl 实现
print("[1] 用 curl 获取初始 cookie ...")
subprocess.run(["curl", "-s", "-o", "/dev/null", "-c", "/tmp/bdck.txt",
                "-A", UA, share_url], check=True)

def curl(args, extra_hdr=None):
    cmd = ["curl", "-s", "--max-time", "30", "-A", UA, "-b", "/tmp/bdck.txt",
           "-c", "/tmp/bdck.txt", "-e", referer] + args
    if extra_hdr:
        cmd += ["-H", extra_hdr]
    out = subprocess.run(cmd, capture_output=True, check=True)
    return out.stdout.decode("utf-8", "ignore")

# 第二步：验证提取码拿 randsk
print("[2] 验证提取码 ...")
verify_url = ("https://pan.baidu.com/share/verify?surl=%s&t=%d03&channel=chunlei"
              "&web=1&app_id=250528&bdstoken=null&logid=&clienttype=0"
              % (surl, int(time.time())))
vjson = curl(["-d", "pwd=" + pwd, verify_url])
v = json.loads(vjson)
if v.get("errno") != 0:
    print("验证失败:", vjson)
    sys.exit(1)
randsk = v["randsk"]
print("    randsk OK")

# 第三步：用 randsk 重新抓分享页, 提取 uk / shareid
print("[3] 抓取带验证的分享页 ...")
page = curl(["-H", "Cookie: BDCLND=" + randsk, share_url])
open("/tmp/bd_share_page.html", "w", encoding="utf-8").write(page)
print("    页面大小:", len(page))

uk = None
shareid = None
m_uk = re.findall(r'"uk"\s*:\s*"?([0-9]{5,})"?', page)
m_sid = re.findall(r'"shareid"\s*:\s*"?([0-9]{5,})"?', page)
if m_uk:
    uk = m_uk[0]
if m_sid:
    shareid = m_sid[0]
# 兜底: 从 typemap 或本地变量再搜
if not uk:
    m2 = re.findall(r'uk[\'"\s=:]+([0-9]{7,})', page)
    uk = m2[0] if m2 else None
if not shareid:
    m2 = re.findall(r'shareid[\'"\s=:]+([0-9]{7,})', page)
    shareid = m2[0] if m2 else None
print("    uk=%s shareid=%s" % (uk, shareid))

# 若页面已直接内嵌 file_list 就直接用
files_embedded = re.findall(r'"server_filename"\s*:\s*"([^"]+)"', page)
if files_embedded:
    print("[✓] 页面内嵌文件列表:")
    for n in files_embedded[:50]:
        print("   ", n)

# 第四步: 调 share/list 接口
if uk and shareid:
    print("[4] 调 share/list 接口 ...")
    list_url = ("https://pan.baidu.com/share/list?shareid=%s&uk=%s&root=1"
                "&num=1000&channel=chunlei&web=1&app_id=250528&clienttype=0"
                % (shareid, uk))
    ljson = curl(["-H", "Cookie: BDCLND=" + randsk, list_url])
    open("/tmp/bd_share_list.json", "w", encoding="utf-8").write(ljson)
    d = json.loads(ljson)
    if d.get("errno") == 0:
        total = 0
        count_files = 0

        def walk(fid, depth):
            global total, count_files
            if depth > 4:
                return
            if fid is None:
                url = ("https://pan.baidu.com/share/list?shareid=%s&uk=%s&root=1"
                       "&num=1000&channel=chunlei&web=1&app_id=250528&clienttype=0"
                       % (shareid, uk))
            else:
                url = ("https://pan.baidu.com/share/list?shareid=%s&uk=%s&root=0"
                       "&fid=%s&num=1000&channel=chunlei&web=1&app_id=250528&clienttype=0"
                       % (shareid, uk, fid))
            sj = curl(["-H", "Cookie: BDCLND=" + randsk, url])
            try:
                sd = json.loads(sj)
            except Exception:
                print("    " * depth + "!! JSON 解析失败:", sj[:120])
                return
            if sd.get("errno") != 0:
                print("    " * depth + "!! errno:", sj[:120])
                return
            import os
            for f in sorted(sd.get("list", []), key=lambda x: -int(x["size"])):
                sz = int(f["size"])
                name = f["server_filename"]
                if f.get("isdir"):
                    print("    " * depth + "[DIR]  %s/" % name)
                    walk(f["fs_id"], depth + 1)
                else:
                    total += sz
                    count_files += 1
                    if sz > 100 * 1024 ** 2 or count_files <= 10 or depth <= 1:
                        print("    " * depth + "       %10.2fGB  %s" % (sz / 1024 ** 3, name))
                    elif count_files % 200 == 0:
                        print("    " * depth + "       ... 已列 %d 个文件" % count_files)

        walk(None, 0)
        print("文件总数: %d, 总大小: %.2f GB" % (count_files, total / 1024 ** 3))
    else:
        print("list errno:", ljson[:200])
else:
    print("!! 未取到 uk/shareid, 请检查 /tmp/bd_share_page.html")
