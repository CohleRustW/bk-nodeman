# -*- coding: utf-8 -*-
"""
TencentBlueKing is pleased to support the open source community by making 蓝鲸智云-节点管理(BlueKing-BK-NODEMAN) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at https://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

from apps.node_man import constants

alive_ips = ["127.0.0.1", "127.0.0.2"]
abnormal_ips = ["127.0.0.3", "127.0.0.4"]
MULTI_GET_AGENT_ALIVE_STATUS = [
    {f"0:{inner_ip}": {"ip": {inner_ip}, "bk_cloud_id": 0, "bk_agent_alive": constants.BkAgentStatus.ALIVE}}
    for inner_ip in alive_ips
]

MULTI_GET_AGENT_ALIVE_INFO = [
    {
        f"0:{inner_ip}": {
            "ip": {inner_ip},
            "version": "V0.01R060D38",
            "bk_cloud_id": 0,
            "parent_ip": {inner_ip},
            "parent_port": 50000,
        }
        for inner_ip in alive_ips
    }
]
