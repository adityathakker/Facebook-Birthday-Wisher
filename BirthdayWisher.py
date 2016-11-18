'''
Project Title: Facebook Birthday Wisher
Developer: AdityaThakker (Github UserName: @adityathakker) 
Website: http://www.adityathakker.com
Github Repo: https://github.com/adityathakker/Facebook-Birthday-Wisher
'''

import json
import os
import pickle
import random
import re
import socket
import time
from datetime import datetime

import requests
import requests.utils
from bs4 import BeautifulSoup
from bs4 import Comment
from termcolor import colored

# URLs
login_url = "https://m.facebook.com/login.php?login_attempt=1"
send_message_url = "https://www.facebook.com/messaging/send/"
fb_url = "https://www.facebook.com"
fb_mobile_url = "https://m.facebook.com/"
user_info_url = "https://www.facebook.com/chat/user_info/"
birthday_url = "https://www.facebook.com/events/birthdays"
history_file_name = ".history"
account_language = "https://www.facebook.com/ajax/settings/language/account.php?dpr=1"

# Change this to whatever you want
my_language = "en_US"

list_of_user_agents = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Version/8.0.5 Safari/601.1.10"
]


class BirthdayWisher(object):
    def __init__(self, email, password):

        if not (email and password):
            raise Exception("Email And Password Are Both Needed")

        self.email = email
        self.password = password
        self.__session = requests.session()
        self.__request_counter = 1
        self.__seq = "0"
        self.__default_payload = {}
        self.__client = 'mercury'
        user_agent = random.choice(list_of_user_agents)
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': fb_url,
            'Origin': fb_url,
            'User-Agent': user_agent,
            'Connection': 'keep-alive',
        }

        print(colored("Logging In To Facebook...", "yellow"))

        for i in range(1, 4):
            if not self.__login():
                print(colored(str(i) + ". Attempt Failed. Retrying...", "red"))
                time.sleep(random.randint(1, 3))
                continue
            else:
                print(colored("Login was Successful", "green"))
                break
        else:
            raise Exception("Login has Failed. Please Check Email and Password")

        self.threads = []

    @staticmethod
    def is_connected():
        try:
            socket.create_connection(("www.facebook.com", 80))
            return True
        except OSError:
            pass
        return False

    def _set_ttstamp(self):
        for i in self.fb_dtsg:
            self.ttstamp += str(ord(i))
        self.ttstamp += '2'

    @staticmethod
    def digit_to_char(digit):
        if digit < 10:
            return str(digit)
        return chr(ord('a') + digit - 10)

    def str_base(self, number, base):
        if number < 0:
            return '-' + self.str_base(-number, base)
        (d, m) = divmod(number, base)
        if d > 0:
            return self.str_base(d, base) + self.digit_to_char(m)
        return self.digit_to_char(m)

    def __generate_payload(self, query):
        payload = self.__default_payload.copy()
        if query:
            payload.update(query)
        payload['__req'] = self.str_base(self.__request_counter, 36)
        payload['seq'] = self.__seq
        self.__request_counter += 1
        return payload

    def __get(self, url, query=None):
        payload = self.__generate_payload(query)
        return self.__session.get(url, headers=self.headers, params=payload, timeout=20)

    def __post(self, url, query=None):
        payload = self.__generate_payload(query)
        return self.__session.post(url, headers=self.headers, data=payload, timeout=20)

    def __login(self):
        if not (self.email and self.password):
            raise Exception("Email And Password Are Both Required")

        soup = BeautifulSoup(self.__get(fb_mobile_url).text, "lxml")
        data = dict((elem['name'], elem['value']) for elem in soup.findAll("input") if
                    elem.has_attr('value') and elem.has_attr('name'))
        data['email'] = self.email
        data['pass'] = self.password
        data['login'] = 'Log In'

        self.__request_counter += 1
        response = self.__post(login_url, data)

        if 'home' in response.url:
            self.client_id = hex(int(random.random() * 2147483648))[2:]
            self.start_time = int(time.time() * 1000)
            # logged in users facebook user id
            self.uid = int(self.__session.cookies['c_user'])
            self.user_channel = "p_" + str(self.uid)
            self.ttstamp = ''

            response = self.__get(fb_url)
            soup = BeautifulSoup(response.text, "lxml")
            self.fb_dtsg = soup.find("input", {'name': 'fb_dtsg'})['value']
            self._set_ttstamp()

            # Set default payload
            self.__default_payload['__rev'] = int(response.text.split('"revision":', 1)[1].split(",", 1)[0])
            self.__default_payload['__user'] = self.uid
            self.__default_payload['__a'] = '1'
            self.__default_payload['ttstamp'] = self.ttstamp
            self.__default_payload['fb_dtsg'] = self.fb_dtsg

            self.form = {
                'channel': self.user_channel,
                'partition': '-2',
                'clientid': self.client_id,
                'viewer_uid': self.uid,
                'uid': self.uid,
                'state': 'active',
                'format': 'json',
                'idle': 0,
                'cap': '8'
            }

            self.prev = int(time.time() * 1000)
            self.tmp_prev = int(time.time() * 1000)
            self.last_sync = int(time.time() * 1000)
            return True
        else:
            return False

    @staticmethod
    def __generate_offline_threading_id():
        ret = int(time.time() * 1000)
        value = int(random.random() * 4294967295)
        string = ("0000000000000000000000" + bin(value))[-22:]
        msgs = bin(ret) + string
        return str(int(msgs, 2))

    def __send(self, recipient_id, message=None):
        message_and_OTID = self.__generate_offline_threading_id()
        timestamp = int(time.time() * 1000)
        date = datetime.now()
        data = {
            'client': self.__client,
            'action_type': 'ma-type:user-generated-message',
            'author': 'fbid:' + str(self.uid),
            'timestamp': timestamp,
            'timestamp_absolute': 'Today',
            'timestamp_relative': str(date.hour) + ":" + str(date.minute).zfill(2),
            'timestamp_time_passed': '0',
            'is_unread': False,
            'is_cleared': False,
            'is_forward': False,
            'is_filtered_content': False,
            'is_filtered_content_bh': False,
            'is_filtered_content_account': False,
            'is_filtered_content_quasar': False,
            'is_filtered_content_invalid_app': False,
            'is_spoof_warning': False,
            'source': 'source:chat:web',
            'source_tags[0]': 'source:chat',
            'body': message,
            'html_body': False,
            'ui_push_phase': 'V3',
            'status': '0',
            'offline_threading_id': message_and_OTID,
            'message_id': message_and_OTID,
            'threading_id': "<%s:%s-%s@mail.projektitan.com>" % (
                time.time() * 1000, int(random.random() * 4294967295), self.client_id),
            'ephemeral_ttl_mode:': '0',
            'manual_retry_cnt': '0',
            'signatureID': hex(int(random.random() * 2147483648)),
            'has_attachment': False,
            'other_user_fbid': recipient_id,
            'specific_to_list[0]': 'fbid:' + str(recipient_id),
            'specific_to_list[1]': 'fbid:' + str(self.uid),

        }

        response = self.__post(send_message_url, data)

        print("Send Data")
        print(data)
        return response.ok

    def __get_user_info(self, user_id):
        data = {"ids[0]": user_id}
        response = self.__post(user_info_url, data)
        info = json.loads(re.sub(r"^[^{]*", '', response.text, 1))
        full_data = [details for profile, details in info['payload']['profiles'].items()]
        if len(full_data) == 1:
            full_data = full_data[0]
        return full_data

    def __extract_birthday_ids(self):
        response = self.__get(birthday_url)
        soup = BeautifulSoup(response.text, "lxml")

        codes = soup.findAll("code")
        code = str()
        for each_code in codes:
            if "events_birthday_view" in str(each_code):
                code = each_code
                break

        comments = code.findAll(text=lambda text: isinstance(text, Comment))
        birthday_div = comments[0]

        try:
            soup = BeautifulSoup(birthday_div, "lxml")
            ul_element = soup.find("ul", {"class": "_3ng0"})
            all_birthdays_div = ul_element.findAll("div", {"class": "clearfix _3ng1"})

            user_ids = list()
            for each_birthday_div in all_birthdays_div:
                name_div = each_birthday_div.find("div", {"class": "_3ng2"})
                name_a = name_div.find("a")
                user_id = str(name_a["data-hovercard"])
                user_id = user_id[28:]
                # print(user_id)
                user_ids.append(user_id)
            return user_ids
        except Exception as e:
            return list()

    def wish(self):
        if os.path.exists(history_file_name):
            history_dict = pickle.load(open(history_file_name, "r"))
            if time.strftime("%x") == history_dict["last_executed"]:
                print(colored("Today's Greetings Were Already Sent", "yellow"))
                self.change_language()
                print(colored("Exiting...", "red"))
                return False

        if self.is_connected():
            user_ids = self.__extract_birthday_ids()
            if len(user_ids) > 0:
                for user_id in user_ids:
                    data = self.__get_user_info(user_id)
                    self.__send(user_id, "Happy Birthday!")
                    print(colored("Greetings Sent to " + data["firstName"], "blue"))

                history_dict = dict()
                history_dict["last_executed"] = time.strftime("%x")
                pickle.dump(history_dict, open(history_file_name, "w"))

                self.change_language()
                print(colored("Exiting...", "red"))
                return True
            else:
                self.change_language()
                print(colored("No Birthday's Today", "blue"))
                print(colored("Exiting...", "red"))
                return False
        else:
            print(colored("No Internet Connection", "red"))
            print(colored("Exiting...", "red"))
            return False

    # After every request my language gets changed to local language
    # So I have to manually change back my language to English
    def change_language(self):
        data = dict()
        data["new_language"] = my_language
        data["new_fallback_language"] = ""
        data["__dyn"] = ""
        data["__af"] = 0
        data["__be"] = -1
        data["__pc"] = "PHASED:DEFAULT"
        self.__post(account_language, data)
