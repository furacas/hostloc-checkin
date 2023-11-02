import os
import pickle
import random
from os import listdir

# import ddddocr

import time
import re
import requests
import sys
from loguru import logger


USER_AGENT = os.getenv("HOST_LOC_USER_AGENT","Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")


class Login:
    def __init__(self, hostname, username, password, questionid='0', answer=None, cookies_flag=True):
        self.session = requests.session()
        self.session.headers.update({
                                        'User-Agent': USER_AGENT})
        self.hostname = hostname
        self.username = str(username)
        self.password = str(password)

        self.questionid = questionid
        self.answer = answer
        self.cookies_flag = cookies_flag
        # self.ocr = ddddocr.DdddOcr()

    def form_hash(self):
        rst = self.session.get(f'https://{self.hostname}/member.php?mod=logging&action=login').text
        loginhash = re.search(r'<div id="main_messaqge_(.+?)">', rst).group(1)
        formhash = re.search(r'<input type="hidden" name="formhash" value="(.+?)" />', rst).group(1)
        logger.info(f'loginhash : {loginhash} , formhash : {formhash} ')
        return loginhash, formhash

    def verify_code_once(self):
        rst = self.session.get(
            f'https://{self.hostname}/misc.php?mod=seccode&action=update&idhash=cSA&0.3701502461393815&modid=member::logging').text
        update = re.search(r'update=(.+?)&idhash=', rst).group(1)

        code_headers = {
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'hostname': f'{self.hostname}',
            'Referer': f'https://{self.hostname}/member.php?mod=logging&action=login',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': USER_AGENT
        }
        rst = self.session.get(f'https://{self.hostname}/misc.php?mod=seccode&update={update}&idhash=cSA',
                               headers=code_headers)

        # return  self.ocr.classification(rst.content)
        return "1234"

    def verify_code(self, num=10):
        while num > 0:
            num -= 1
            code = self.verify_code_once()
            verify_url = f'https://{self.hostname}/misc.php?mod=seccode&action=check&inajax=1&modid=member::logging&idhash=cSA&secverify={code}'
            res = self.session.get(verify_url).text

            if 'succeed' in res:
                logger.info('验证码识别成功，验证码:' + code)
                return code
            else:
                logger.info('验证码识别失败，重新识别中...')

        logger.error('验证码获取失败，请增加验证次数或检查当前验证码识别功能是否正常')
        return ''

    def account_login_without_verify(self):

        loginhash, formhash = self.form_hash()
        login_url = f'https://{self.hostname}/member.php?mod=logging&action=login&loginsubmit=yes&loginhash={loginhash}&inajax=1'
        formData = {
            'formhash': formhash,
            'referer': f'https://{self.hostname}/',
            'username': self.username,
            'password': self.password,
            'handlekey': 'ls',
        }
        login_rst = self.session.post(login_url, data=formData).text
        if 'succeed' in login_rst:
            logger.info('登陆成功')
            return True
        else:
            logger.info('登陆失败，请检查账号或密码是否正确')
            return False

    def account_login(self):
        try:
            if self.account_login_without_verify():
                return True
        except Exception:
            logger.error('存在验证码，登陆失败，准备获取验证码中', exc_info=True)

        code = self.verify_code()
        if code == '':
            return False

        loginhash, formhash = self.form_hash()
        login_url = f'https://{self.hostname}/member.php?mod=logging&action=login&loginsubmit=yes&loginhash={loginhash}&inajax=1'
        formData = {
            'formhash': formhash,
            'referer': f'https://{self.hostname}/',
            'loginfield': self.username,
            'username': self.username,
            'password': self.password,
            'questionid': self.questionid,
            'answer': self.answer,
            'cookietime': 2592000,
            'seccodehash': 'cSA',
            'seccodemodid': 'member::logging',
            'seccodeverify': code,  # verify code
        }
        login_rst = self.session.post(login_url, data=formData).text
        if 'succeed' in login_rst:
            logger.info('登陆成功')
            return True
        else:
            logger.info('登陆失败，请检查账号或密码是否正确')
            return False

    def cookies_login(self):
        cookies_name = '.cookies-' + self.username
        if cookies_name in listdir():
            try:
                with open(cookies_name, 'rb') as f:
                    self.session = pickle.load(f)
                response = self.session.get(f'https://{self.hostname}/home.php?mod=space').text

                if "退出" in response and "登录" not in response:
                    logger.info('从文件中恢复Cookie成功，跳过登录。')
                    return True
            except Exception:
                logger.warning('Cookie失效，使用账号密码登录。')
        else:
            logger.info('初次登录未发现Cookie，使用账号密码登录。')
        return False

    def go_home(self):
        return self.session.get(f'https://{self.hostname}/forum.php').text

    def get_conis(self):
        try:
            res = self.session.get(
                f'https://{self.hostname}/home.php?mod=spacecp&ac=credit&showcredit=1&inajax=1&ajaxtarget=extcreditmenu_menu').text
            coins = re.search(r'<span id="hcredit_2">(.+?)</span>', res).group(1)
            logger.info(f'当前金币数量：{coins}')
        except Exception:
            logger.error('获取金币数量失败！', exc_info=True)

    def main(self):

        try:
            if self.cookies_flag and self.cookies_login():
                logger.info('成功使用cookies登录')
            else:
                self.account_login()
            res = self.go_home()
            self.post_formhash = re.search(r'<input type="hidden" name="formhash" value="(.+?)" />', res).group(1)
            credit = re.search(r' class="showmenu">(.+?)</a>', res).group(1)
            logger.info(f'{credit},提交文章formhash:{self.post_formhash}')

            self.get_conis()

            cookies_name = '.cookies-' + self.username
            with open(cookies_name, 'wb') as f:
                pickle.dump(self.session, f)
                logger.info('新的Cookie已保存。')

        except Exception:
            logger.error('失败，发生了一个错误！', exc_info=True)
            sys.exit()


class Hostloc:
    def __init__(self, username, password, questionid='0', answer=None, cookies_flag=True):
        self.hostname =  'hostloc.com'
        self.discuz_login = Login(self.hostname, username, password, questionid, answer, cookies_flag)

    def login(self):
        self.discuz_login.main()
        self.session = self.discuz_login.session
        self.formhash = self.discuz_login.post_formhash

    def go_home(self):
        return self.session.get(f'https://{self.hostname}/forum.php').text

    def go_hot(self):
        return self.session.get(f'https://{self.hostname}/forum-45-1.html').text

    def generate_random_numbers(self, start, end, count):
        random_numbers = []
        for _ in range(count):
            random_number = random.randint(start, end)
            random_numbers.append(random_number)
        return random_numbers

    def signin(self):
        signin_url =  f'https://{self.hostname}'
        self.session.get(signin_url)

    def visit_home(self):
        start = 1
        end = 50000
        count = 10

        random_numbers = self.generate_random_numbers(start, end, count)
        for number in random_numbers:
            time.sleep(5)
            signin_url = f'https://{self.hostname}/space-uid-{number}.html'
            self.session.get(signin_url)


if __name__ == '__main__':
    username = os.getenv('HOST_LOC_USER_NAME')
    password = os.getenv('HOST_LOC_PASSWORD')
    hostloc = Hostloc(username, password)
    hostloc.login()
    hostloc.signin()
    hostloc.visit_home()