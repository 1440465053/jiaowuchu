# encoding=utf-8
import re
import json
import requests
from lxml import etree
from hashlib import md5
from urllib import parse
import datetime
requests.packages.urllib3.disable_warnings()


class Chaojiying_Client(object):
    def __init__(self, username, password, soft_id):
        self.username = username
        password =  password.encode('utf8')
        self.password = md5(password).hexdigest()
        self.soft_id = soft_id
        self.base_params = {
            'user': self.username,
            'pass2': self.password,
            'softid': self.soft_id,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
        }

    def PostPic(self, im, codetype):
        """
        im: 图片字节
        codetype: 题目类型 参考 http://www.chaojiying.com/price.html
        """
        params = {
            'codetype': codetype,
        }
        params.update(self.base_params)
        files = {'userfile': ('ccc.jpg', im)}
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', data=params, files=files, headers=self.headers)
        return r.json()

    def PostPic_base64(self, base64_str, codetype):
        """
        im: 图片字节
        codetype: 题目类型 参考 http://www.chaojiying.com/price.html
        """
        params = {
            'codetype': codetype,
            'file_base64':base64_str
        }
        params.update(self.base_params)
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', data=params, headers=self.headers)
        return r.json()

    def ReportError(self, im_id):
        """
        im_id:报错题目的图片ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post('http://upload.chaojiying.net/Upload/ReportError.php', data=params, headers=self.headers)
        return r.json()





class JWSystem:
    session = requests.session()
    session.headers.update({
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
    })
    # proxies = {
    #     "http": "http://127.0.0.1:8888",
    #     "https": "http://127.0.0.1:8888",
    # }
    proxies = None

    def getIntercept(self, url):
        # 处理跨域携带cookie
        cookies = ""
        for key, value in self.session.cookies.items():
            cookies += key + '=' + value + "; "

        headers = {"Origin": "https://jwch.fzu.edu.cn",
                   "Referer": "https://jwch.fzu.edu.cn/",
                   "cookie": cookies
                   }
        response = self.session.get(url, verify=False, proxies=self.proxies,
                                    headers=headers)
        return response

    def postIntercept(self, url, data):
        # 处理跨域携带cookie
        cookies = ""
        for key, value in self.session.cookies.items():
            cookies += key + '=' + value + "; "

        headers = {"Origin": "https://jwch.fzu.edu.cn",
                   "Referer": "https://jwch.fzu.edu.cn/",
                   'X-Requested-With': 'XMLHttpRequest',
                   "cookie": cookies
                   }
        response = self.session.post(url, data=data, verify=False, proxies=self.proxies,
                                     headers=headers)
        return response

    def getVerifyCode(self):
        # 获取验证码
        url = "https://jwcjwxt1.fzu.edu.cn/plus/verifycode.asp?n=0.11646368822551079"
        res = self.session.get(url, verify=False, proxies=self.proxies).content
        # with open('yzm.png', 'wb') as f:
        #     f.write(res)

        chaojiying = Chaojiying_Client('xxxxx', 'xxxxx', '940956')  # 用户中心>>软件ID 生成一个替换 96001
        # print(chaojiying.PostPic(res, 6001))  # 1902 验证码类型  官方网站>>价格体系 3.4+版 print 后要加()
        # print chaojiying.PostPic(base64_str, 1902)  #此处为传入 base64代码
        result = chaojiying.PostPic(res, 6001)
        # print(result)
        return result['pic_str']



    def SSOLogin(self, token):
        url = "https://jwcjwxt2.fzu.edu.cn/Sfrz/SSOLogin"
        resp = self.postIntercept(url, data={"token": token})
        resp.encoding = "gb2312"
        # print(resp.request.headers)
        # print(resp.cookies)
        # print(resp.text)
        return resp.status_code == 200

    def login(self , username , password):
        verifyCode = self.getVerifyCode()#input("请输入验证码：")
        # 打印验证码
        # print(verifyCode)
        url = "https://jwcjwxt1.fzu.edu.cn/logincheck.asp"
        data = {
            "muser": username ,
            "passwd": password,
            "Verifycode": verifyCode
        }
        response = self.postIntercept(url, data=data)
        response.encoding = "utf-8"
        res = response.text
        index_url = re.findall("window.location.href =  '(.*?)';", res)
        if index_url:
            index_url = index_url[0]
        else:
            print("账号密码错误")
            return
        token = parse.parse_qs(parse.urlparse(response.url).query)['token'][0]
        self.SSOLogin(token)
        # 获取身份的id
        r = self.getIntercept(index_url)
        idx = parse.parse_qs(parse.urlparse(r.url).query)['id'][0]


        return idx


    def parselTimetable(self , response):
        # 解析课表
        html = etree.HTML(response)
        # html = etree.HTML(open('test.html', 'r', encoding="utf-8").read())
        # 所有课表标签
        wholeSchedule = html.xpath('//table[1]/tr')[2:-1]
        repS = -1
        data = []
        allData = {}
        for whole in wholeSchedule:
            repS += 1
            lineSchedule = []
            for td in whole.xpath('./td'):
                # 获取当前标签所有文本
                text = td.xpath('.//text()')
                if text:
                    text2 = text[0]
                    if text2 == str(repS):
                        text = text[1:]
                    elif text2 == '\xa0' or text2 == '上午' or text2 == '下午' or text2 == '晚上':
                        continue
                scheduleStr = "".join(text) if text else ""
                scheduleStr = scheduleStr
                lineSchedule.append(scheduleStr.replace('[教学大纲|授课计划]', ''))
            data.append(lineSchedule)
        allData['row_data'] = data
        return allData

    def Timetable(self, idx):
        # 获取课表
        url = "https://jwcjwxt2.fzu.edu.cn:81/student/xkjg/wdkb/kb_xs.aspx?id=" + idx
        r = self.getIntercept(url)
        return self.parselTimetable(r.text) 




if __name__ == '__main__':

    jw = JWSystem()
    idx = jw.login("xxxx","xxxxx")
    

'''

https://jwcjwxt1.fzu.edu.cn/logincheck.asp
    location: https://jwcjwxt2.fzu.edu.cn/ssoLogin.asp?token=b527fc07-1c5f-4753-9a13-430121d8fb36&returnurl=https://jwcjwxt2.fzu.edu.cn:81/loginchk_xs.aspx&id=20221031214538823&num=5068&hosturl=https://jwcjwxt2.fzu.edu.cn:81&ssourl=https://jwcjwxt2.fzu.edu.cn
    if https://jwcjwxt2.fzu.edu.cn/Sfrz/SSOLogin == 200:
        window.location.href = https://jwcjwxt2.fzu.edu.cn:81/loginchk_xs.aspx?id=20221031214538823&num=5068&ssourl=https://jwcjwxt2.fzu.edu.cn&hosturl=https://jwcjwxt2.fzu.edu.cn:81
        Location = https://jwcjwxt2.fzu.edu.cn/Home/index?id=2022103121461182212&hosturl=https://jwcjwxt2.fzu.edu.cn:81
'''

