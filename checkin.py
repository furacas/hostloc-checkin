import os
import pickle
import random
from os import listdir

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


    def form_hash(self):
        rst = self.session.get(f'https://{self.hostname}/member.php?mod=logging&action=login').text
        loginhash = re.search(r'<div id="main_messaqge_(.+?)">', rst).group(1)
        formhash = re.search(r'<input type="hidden" name="formhash" value="(.+?)" />', rst).group(1)
        logger.info(f'loginhash : {loginhash} , formhash : {formhash} ')
        return loginhash, formhash


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
            sleep_time = random.randint(5, 10)
            time.sleep(sleep_time)
            visit_url = f'https://{self.hostname}/space-uid-{number}.html'
            self.session.get(visit_url)


if __name__ == '__main__':
    username = os.getenv('HOSTLOC_USERNAME')
    password = os.getenv('HOSTLOC_PASSWORD')
    hostloc = Hostloc(username, password)
    hostloc.login()
    hostloc.signin()
    hostloc.visit_home()