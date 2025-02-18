import json
from nturl2path import url2pathname
from synology_api import auth
from urllib import parse


class UniversalSearch:
    def __init__(self, ip_address, port, username, password, secure=False, cert_verify=False, dsm_version=7, debug=True, otp_code=None):
        self.session = auth.CachableAuthentication(
            ip_address, port, username, password, secure, cert_verify, dsm_version, debug, otp_code)
        self.session.login('Finder')
        self.session.get_api_list('Finder')
        self.finder_list = self.session.app_api_list

        if debug is True:
            print('You are now logged in!')

    def search(self, keyword):
        api_name = 'SYNO.Finder.FileIndexing.Search'
        info = self.finder_list[api_name]
        api_path = info['path']

        req_param = {
            "query_serial": 1,
            "indice": '[]',
            "keyword": json.dumps(f'{keyword}'),
            "orig_keyword": json.dumps(f'{keyword}'),
            "criteria_list": '[]',
            "from": 0,
            "size": 10,
            "fields": '[' +
                '"SYNOMDAcquisitionMake",' +
                '"SYNOMDAcquisitionModel",' +
                '"SYNOMDAlbum",' +
                '"SYNOMDAperture",' +
                '"SYNOMDAudioBitRate",' +
                '"SYNOMDAudioTrackNumber",' +
                '"SYNOMDAuthors",' +
                '"SYNOMDCodecs",' +
                '"SYNOMDContentCreationDate",' +
                '"SYNOMDContentModificationDate",' +
                '"SYNOMDCreator",' +
                '"SYNOMDDurationSecond",' +
                '"SYNOMDExposureTimeString",' +
                '"SYNOMDExtension",' +
                '"SYNOMDFSCreationDate",' +
                '"SYNOMDFSName",' +
                '"SYNOMDFSSize",' +
                '"SYNOMDISOSpeed",' +
                '"SYNOMDLastUsedDate",' +
                '"SYNOMDMediaTypes",' +
                '"SYNOMDMusicalGenre",' +
                '"SYNOMDOwnerUserID",' +
                '"SYNOMDOwnerUserName",' +
                '"SYNOMDRecordingYear",' +
                '"SYNOMDResolutionHeightDPI",' +
                '"SYNOMDResolutionWidthDPI",' +
                '"SYNOMDTitle",' +
                '"SYNOMDVideoBitRate",' +
                '"SYNOMDIsEncrypted"' +
                ']',
            "file_type": "",
            "search_weight_list": '[' +
                '{"field":"SYNOMDWildcard","weight":1},' +
                '{"field":"SYNOMDTextContent","weight":1},' +
                '{"field":"SYNOMDSearchFileName","weight":8.5,"trailing_wildcard":"true"}' +
                ']',
            "sorter_field": "relevance",
            "sorter_direction": "asc",
            "sorter_use_nature_sort": "false",
            "sorter_show_directory_first": "true",
            "api": "SYNO.Finder.FileIndexing.Search",
            "method": "search",
            "version": 1
        }

        return self.session.request_data(api_name, api_path, req_param, method='post')
