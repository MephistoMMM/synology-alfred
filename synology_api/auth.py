import requests
import os
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning

class Authentication:
    def __init__(self, ip_address, port, username, password, secure=False, cert_verify=False, dsm_version=7, debug=True, otp_code=None):
        self._ip_address = ip_address
        self._port = port
        self._username = username
        self._password = password
        self._sid = None
        self._login_app = ''
        self._session_expire = True
        self._verify = cert_verify
        self._version = dsm_version
        self._debug = debug
        self._otp_code = otp_code
        if self._verify is False:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        schema = 'https' if secure else 'http'
        self._base_url = '%s://%s:%s/webapi/' % (
            schema, self._ip_address, self._port)

        self.full_api_list = {}
        self.app_api_list = {}

    def verify_cert_enabled(self):
        return self._verify

    def login(self, application):
        login_api = 'auth.cgi?api=SYNO.API.Auth'
        param = {'version': self._version, 'method': 'login', 'account': self._username,
                 'passwd': self._password, 'session': application, 'format': 'cookie'}
        if self._otp_code:
            param['otp_code'] = self._otp_code

        if not self._session_expire:
            if self._sid is not None:
                self._session_expire = False
                if self._debug is True:
                    return 'User already logged'
        else:
            session_request = requests.post(
                self._base_url + login_api, param, verify=self._verify)
            self._sid = session_request.json()['data']['sid']
            self._session_expire = False
            if self._debug is True:
                return 'User logging... New session started!'

    def logout(self, application):
        logout_api = 'auth.cgi?api=SYNO.API.Auth'
        param = {'version': '2', 'method': 'logout', 'session': application}

        response = requests.get(
            self._base_url + logout_api, param, verify=self._verify)
        if response.json()['success'] is True:
            self._session_expire = True
            self._sid = None
            if self._debug is True:
                return 'Logged out'
        else:
            self._session_expire = True
            self._sid = None
            if self._debug is True:
                return 'No valid session is open'

    def get_api_list(self, app=None):
        query_path = 'query.cgi?api=SYNO.API.Info'
        list_query = {'version': '1', 'method': 'query', 'query': 'all'}

        response = requests.get(
            self._base_url + query_path, list_query, verify=self._verify).json()

        if app is not None:
            for key in response['data']:
                if app.lower() in key.lower():
                    self.app_api_list[key] = response['data'][key]
        else:
            self.full_api_list = response['data']

        return

    def show_api_name_list(self):
        prev_key = ''
        for key in self.full_api_list:
            if key != prev_key:
                print(key)
                prev_key = key
        return

    def show_json_response_type(self):
        for key in self.full_api_list:
            for sub_key in self.full_api_list[key]:
                if sub_key == 'requestFormat':
                    if self.full_api_list[key]['requestFormat'] == 'JSON':
                        print(key + '   Returns JSON data')
        return

    def search_by_app(self, app):
        print_check = 0
        for key in self.full_api_list:
            if app.lower() in key.lower():
                print(key)
                print_check += 1
                continue
        if print_check == 0:
            print('Not Found')
        return

    def request_data(self, api_name, api_path, req_param, method=None, response_json=True):  # 'post' or 'get'

        # Convert all boolean in string in lowercase because Synology API is waiting for "true" or "false"
        for k, v in req_param.items():
            if isinstance(v, bool):
                req_param[k] = str(v).lower()

        if method is None:
            method = 'get'

        req_param['_sid'] = self._sid

        if method == 'get':
            url = ('%s%s' % (self._base_url, api_path)) + '?api=' + api_name
            response = requests.get(url, req_param, verify=self._verify)

            if response_json is True:
                return response.json()
            else:
                return response

        elif method == 'post':
            url = ('%s%s' % (self._base_url, api_path)) + '?api=' + api_name
            response = requests.post(url, req_param, verify=self._verify)

            if response_json is True:
                return response.json()
            else:
                return response

    @property
    def sid(self):
        return self._sid

    @property
    def base_url(self):
        return self._base_url

class CachableAuthentication(Authentication):

    def __init__(self, ip_address, port, username, password,
               secure=False,
               cert_verify=False,
               dsm_version=7,
               debug=True,
               otp_code=None,
               cachedir='~/.cache/synology_api'):
        super().__init__(
            ip_address, port, username, password, secure, cert_verify, dsm_version, debug, otp_code)
        self.cachedir = os.path.expanduser(cachedir)
        self.cachefile = os.path.join(self.cachedir, "session.json")
        self.cached_session = {}

    def _load(self):
        if not os.path.exists(self.cachedir):
            os.makedirs(self.cachedir, 0o750, True)
        if not os.path.exists(self.cachefile):
            self.cached_session = {}
            return

        with open(self.cachefile, 'r') as f:
            self.cached_session = json.load(f)

    def _store(self):
        if len(self.cached_session) < 1:
            return
        if not os.path.exists(self.cachedir):
            os.makedirs(self.cachedir, 0o750, True)

        with open(self.cachefile, 'w') as f:
            json.dump(self.cached_session, f)

    @property
    def session(self) -> dict:
        if len(self.cached_session) == 0:
            self._load()
        return self.cached_session

    def get_api_list(self, app=None):
        # load api list from cache
        full_info = self.session.get('full_api_list')
        if full_info is None:
            # request webapi to get full api list
            query_path = 'query.cgi?api=SYNO.API.Info'
            list_query = {'version': '1', 'method': 'query', 'query': 'all'}

            response = requests.get(
                self._base_url + query_path, list_query, verify=self._verify).json()

            full_info = response['data']
            self.session['full_api_list'] = full_info
            self._store()

        self.app_api_list = full_info
        self.full_api_list = full_info

    def login(self, application):
        self._login_app = application

        # load sid from cache
        sid = self.session.get('sids', {}).get(application)
        if sid is not None :
            self._sid = sid
            self._session_expire = False
            if self._debug is True:
                return 'User already logged with cache session id'

        # request webapi to login
        result = super().login(application)
        if self.session.get('sids') is None:
            self.session['sids'] = {}
        self.session['sids'][application] = self._sid
        self._store()
        return result

    def invalid_sid(self, application):
        self.session['sids'][application] = None
        self._session_expire = True

    def request_data(self, api_name, api_path, req_param, method=None, response_json=True):
        response = super().request_data(
            api_name, api_path, req_param, method, response_json)
        json_data = response if response_json else response.json()

        if json_data.get('success', False) :
            return response

        # normal error just return
        if  119 != json_data.get('error', {}).get('code'):
            return response

        # invalid session error(119), try to re-login
        self.invalid_sid(self._login_app)
        self.login(self._login_app)

        # request again
        return super().request_data(
            api_name, api_path, req_param, method, response_json)
