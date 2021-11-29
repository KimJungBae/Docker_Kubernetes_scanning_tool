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

import logging


# Dagda logger class

class DagdaLogger(logging.Logger):

    # -- Init
    logging.basicConfig(format='<%(asctime)s> <%(levelname)s> <DagdaServer> <%(module)s> <%(funcName)s:%(lineno)d> ' +
                               '<%(message)s>')                 # levelname => 에러 및 INFO 관련 출력 == 이곳에서는 getLevel에서 디버그로 햇으니 그에따른 출력이 이루어짐.
    _logger = logging.getLogger('DagdaLogger')                  # 로거 이름 설정
    _logger.setLevel('DEBUG')                                   # 디버그 된 것에 대한 로그 출력

    # -- Static methods

    @staticmethod
    def get_logger():
        return DagdaLogger._logger
