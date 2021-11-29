#
# Licensed to Dagda under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Dagda licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import io
from datetime import date
from threading import Thread
from log.dagda_logger import DagdaLogger
from api.internal.internal_server import InternalServer
from vulnDB.ext_source_util import get_bug_traqs_lists_from_file
from vulnDB.ext_source_util import get_bug_traqs_lists_from_online_mode
from vulnDB.ext_source_util import get_cve_list_from_file
from vulnDB.ext_source_util import get_exploit_db_list_from_csv
from vulnDB.ext_source_util import get_http_resource_content
from vulnDB.bid_downloader import bid_downloader
from vulnDB.ext_source_util import get_rhsa_and_rhba_lists_from_file


# Static field
next_year = date.today().year + 1   # 해당 연도 cve 없으면 내년으로 


# DBComposer class
class DBComposer:

    # -- Public methods

    # DBComposer Constructor
    def __init__(self):
        super(DBComposer, self).__init__()
        self.mongoDbDriver = InternalServer.get_mongodb_driver() # 몽고db 호출

    # Compose vuln DB
    def compose_vuln_db(self):
        if InternalServer.is_debug_logging_enabled():
            DagdaLogger.get_logger().debug('ENTRY to the method for composing VulnDB') # 몽고 db내에 vuln_database 연결 확인

        # -- CVE
        # Adding or updating CVEs
        if InternalServer.is_debug_logging_enabled():   # 리스팅 해놓은 cve 데이터를 몽고db에 업데이트 확인.
            DagdaLogger.get_logger().debug('Updating CVE collection ...')

        first_year = self.mongoDbDriver.remove_only_cve_for_update()
        for i in range(first_year, next_year):
            DBComposer._threaded_cve_gathering(self.mongoDbDriver, i) # 연도별 cve 확인.

        if InternalServer.is_debug_logging_enabled():
            DagdaLogger.get_logger().debug('CVE collection updated') # 전부 cve관련 dagda내에서 log 업데이트 및 확인.

        # -- Exploit DB
        # Adding or updating Exploit_db and Exploit_db info
        if InternalServer.is_debug_logging_enabled():
            DagdaLogger.get_logger().debug('Updating Exploit DB collection ...')

        self.mongoDbDriver.delete_exploit_db_collection()           # 몽고 db 특성상 무결성 체크가 안되서 업데이트 할때 정보를 모두 지우고 다시 받아 오는 모습.
        self.mongoDbDriver.delete_exploit_db_info_collection()
        csv_content = get_http_resource_content(
            'https://raw.githubusercontent.com/offensive-security/exploit-database/master/files_exploits.csv') # windows, linux os관련 취약점 피드(콤마로 되어 있어서 csv로 관리 하는 듯함.)
        exploit_db_list, exploit_db_info_list = get_exploit_db_list_from_csv(csv_content.decode("utf-8"))
        self.mongoDbDriver.bulk_insert_exploit_db_ids(exploit_db_list)          # db insert(삽입) cve
        self.mongoDbDriver.bulk_insert_exploit_db_info(exploit_db_info_list)    # db insert(삽입) cve_)_info

        if InternalServer.is_debug_logging_enabled():
            DagdaLogger.get_logger().debug('Exploit DB collection updated')

        # -- RHSA (Red Hat Security Advisory) and RHBA (Red Hat Bug Advisory)
        # Adding or updating rhsa and rhba collections
        if InternalServer.is_debug_logging_enabled():           # red hat 관련 피드 => 위와 다르게 두가지 특성이 있는 db가 있다.
            DagdaLogger.get_logger().debug('Updating RHSA & RHBA collections ...')

        self.mongoDbDriver.delete_rhba_collection()
        self.mongoDbDriver.delete_rhba_info_collection()
        self.mongoDbDriver.delete_rhsa_collection()
        self.mongoDbDriver.delete_rhsa_info_collection()
        bz2_file = get_http_resource_content('https://www.redhat.com/security/data/oval/rhsa.tar.bz2')
        rhsa_list, rhba_list, rhsa_info_list, rhba_info_list = get_rhsa_and_rhba_lists_from_file(bz2_file)
        self.mongoDbDriver.bulk_insert_rhsa(rhsa_list)
        self.mongoDbDriver.bulk_insert_rhba(rhba_list)
        self.mongoDbDriver.bulk_insert_rhsa_info(rhsa_info_list)
        self.mongoDbDriver.bulk_insert_rhba_info(rhba_info_list)

        if InternalServer.is_debug_logging_enabled():
            DagdaLogger.get_logger().debug('RHSA & RHBA collections updated')

        # -- BID ==> bid_downloader가 정상적으로 실행되어 로컬내에 리스팅 된 후...
        # Adding BugTraqs from 20180328_sf_db.json.gz, where 103525 is the max bid in the gz file
        if InternalServer.is_debug_logging_enabled():
            DagdaLogger.get_logger().debug('Updating BugTraqs Id collection ...')

        max_bid = self.mongoDbDriver.get_max_bid_inserted()
        bid_thread = Thread(target=DBComposer._threaded_preprocessed_bid_gathering, args=(self.mongoDbDriver, max_bid))
        if max_bid < 103525:        # 103525 전체 feed 갯수 인듯 싶은데, 개발 당시 특정 년도까지의 시점인듯함.
            bid_thread.start()
            # Set the new max bid
            max_bid = 103525

        # Updating BugTraqs from http://www.securityfocus.com/
        bid_items_array, bid_detail_array = get_bug_traqs_lists_from_online_mode(bid_downloader(first_bid=max_bid+1,
                                                                                                last_bid=104000))
        # Insert BIDs
        if len(bid_items_array) > 0:
            for bid_items_list in bid_items_array:
                self.mongoDbDriver.bulk_insert_bids(bid_items_list)
                bid_items_list.clear()
        # Insert BID details
        if len(bid_detail_array) > 0:
            self.mongoDbDriver.bulk_insert_bid_info(bid_detail_array)
            bid_detail_array.clear()

        # Wait for bid_thread
        if bid_thread.is_alive():
            bid_thread.join()

        if InternalServer.is_debug_logging_enabled():
            DagdaLogger.get_logger().debug('BugTraqs Id collection updated')

        if InternalServer.is_debug_logging_enabled():
            DagdaLogger.get_logger().debug('EXIT from the method for composing VulnDB')

    # Get CVEs thread
    @staticmethod               # 객체 생성 없이 바로 method 사용 가능.
    def _threaded_cve_gathering(mongoDbDriver, i):
        if InternalServer.is_debug_logging_enabled():
            DagdaLogger.get_logger().debug('... Including CVEs - ' + str(i))

        compressed_content = get_http_resource_content(         # NATIONAL VULNERABILITY DATABASE라는 곳에서 해당 cve를 json 형식 으로 가져옴.
            "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-" + str(i) + ".json.gz")
        cve_list, cve_ext_info_list = get_cve_list_from_file(compressed_content, i)     # 추가된 정보가 있으면 insert하라.
        if len(cve_list) > 0:
            mongoDbDriver.bulk_insert_cves(cve_list)
        if len(cve_ext_info_list) > 0:
            mongoDbDriver.bulk_insert_cves_info(cve_ext_info_list)

    # Get preprocessed BIDs thread
    @staticmethod
    def _threaded_preprocessed_bid_gathering(mongoDbDriver, max_bid):
        # Clean
        if max_bid != 0:
            mongoDbDriver.delete_bid_collection()
            mongoDbDriver.delete_bid_info_collection()
        # Adding BIDs
        compressed_file = io.BytesIO(get_http_resource_content(
            "https://github.com/eliasgranderubio/bidDB_downloader/raw/master/bonus_track/20180328_sf_db.json.gz")) # 해당 깃 사이트에서 bid_downloader를 가져온 것으로 
        bid_items_array, bid_detail_array = get_bug_traqs_lists_from_file(compressed_file)                         # 전체적인 정보 업데이트는 이곳에서 이루어진다.
        # Insert BIDs
        for bid_items_list in bid_items_array:
            mongoDbDriver.bulk_insert_bids(bid_items_list)
            bid_items_list.clear()
        # Insert BID details
        mongoDbDriver.bulk_insert_bid_info(bid_detail_array)
        bid_detail_array.clear()
