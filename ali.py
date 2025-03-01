import re
import json
import time
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
    "Rererer": "https://www.aliyundrive.com/",
    "Content-Type": "application/json"
}

class Ali:
    # 获取token
    def refresh_token(self, token, delFile=False):
        params = {}
        header = headers.copy()
        try:
            r = requests.post(url='https://auth.aliyundrive.com/v2/account/token',
                              json={'grant_type': 'refresh_token', 'refresh_token': token},
                              headers=header,
                              timeout=10)
            if r.status_code != 200:
                return {}
            jo = json.loads(r.text)
            params['token'] = jo['refresh_token']
            params['authorization'] = '{} {}'.format(jo['token_type'], jo['access_token'])
            params['user_id'] = jo['user_id']
            params['drive_id'] = jo['default_drive_id']
            params['export_in'] = jo['expires_in']
            tokenDict = self.refresh_opentoken(params)
            if 'export_in' in tokenDict:
                del tokenDict['export_in']
            self.check_in(params)
            if delFile:
                self.delFile(params)
        except:
            tokenDict = {}
        return tokenDict

    # 获取opentoken
    def refresh_opentoken(self, params):
        tokenDict = params.copy()
        header = headers.copy()
        header['authorization'] = tokenDict['authorization']
        try:
            r = requests.post(
                url='https://open.aliyundrive.com/oauth/users/authorize?client_id=76917ccccd4441c39457a04f6084fb2f&redirect_uri=https://alist.nn.ci/tool/aliyundrive/callback&scope=user:base,file:all:read,file:all:write&state=',
                json={
                    'authorize': 1,
                    'scope': 'user:base,file:all:read,file:all:write'
                },
                headers=header)
            code = re.search(r'code=(.*?)\"', r.text).group(1)
            r = requests.post(url='https://api.nn.ci/alist/ali_open/code',
                              json={
                                  'code': code,
                                  'grant_type': 'authorization_code'
                              },
                              headers=header)
            jo = json.loads(r.text)
            openexport_in = jo['expires_in']
            opentoken = jo['refresh_token']
            opauthorization = '{} {}'.format(jo['token_type'], jo['access_token'])
        except:
            openexport_in = 7200
            opentoken = ''
            opauthorization = ''
        tokenDict['opentoken'] = opentoken
        tokenDict['opauthorization'] = opauthorization
        tokenDict['expires_at'] = int(int(time.time()) + min(tokenDict['export_in'], openexport_in)/2)
        return tokenDict

    # 签到、领奖
    def check_in(self, params):
        tokenDict = params.copy()
        header = headers.copy()
        header['authorization'] = tokenDict['authorization']
        r = requests.post(url='https://member.aliyundrive.com/v1/activity/sign_in_list',
                          json={"grant_type": "refresh_token", "refresh_token": tokenDict['token']},
                          headers=header,
                          timeout=10)
        for day in r.json()['result']['signInLogs']:
            if day['isReward'] is False and day['status'] == 'normal':
                signInDay = day['day']
                requests.post(url='https://member.aliyundrive.com/v1/activity/sign_in_reward',
                              json={"grant_type": "refresh_token", "refresh_token": tokenDict['token'], "signInDay": signInDay},
                              headers=header,
                              timeout=10)
        return

    # 删除根目录文件
    def delFile(self, params):
        tokenDict = params.copy()
        header = headers.copy()
        header['authorization'] = tokenDict['authorization']
        r = requests.post(url='https://api.aliyundrive.com/adrive/v3/file/list',
                          json={"drive_id": tokenDict['drive_id'], "parent_file_id": "root"},
                          headers=header,
                          timeout=10)
        for item in r.json()['items']:
            if item['type'] == 'file':
                requests.post('https://api.aliyundrive.com/v3/batch',
                              json={"requests":
                                        [{"body": {"drive_id": tokenDict['drive_id'], "file_id": item['file_id']},
                                          "headers": {"Content-Type": "application/json"},
                                          "id": item['file_id'],
                                          "method": "POST",
                                          "url": "/file/delete"}],
                                    "resource": "file"},
                              headers=header,
                              timeout=10)
        return
