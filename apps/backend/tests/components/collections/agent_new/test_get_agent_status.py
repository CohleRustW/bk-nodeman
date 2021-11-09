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

from typing import AnyStr, List, Optional

import mock

from apps.backend.components.collections.agent import GetAgentStatusComponent
from apps.mock_data import api_mkd, common_unit
from apps.mock_data import utils as mock_data_utils
from pipeline.component_framework.test import ComponentTestCase, ExecuteAssertion

from . import utils

gse_mock_client: Optional[api_mkd.gse.unit.GseMockClient] = None
gse_v2_mock_path: AnyStr = "apps.backend.components.collections.agent.client_v2"


class GetAgentStatusTestCase(utils.AgentServiceBaseTestCase):
    def init_mock_client(self):
        self.gse_mock_client = api_mkd.gse.unit.GseMockClient(
            get_agent_status_return=mock_data_utils.MockReturn(
                return_type=mock_data_utils.MockReturnType.RETURN_VALUE.value,
                return_obj=common_unit.gse.MULTI_GET_AGENT_ALIVE_STATUS,
            ),
            get_agent_info_return=mock_data_utils.MockReturn(
                return_type=mock_data_utils.MockReturnType.RETURN_VALUE.value,
                return_obj=common_unit.gse.MULTI_GET_AGENT_ALIVE_INFO,
            ),
        )

    def fetch_succeeded_sub_inst_ids(self) -> List[int]:
        return self.common_inputs["subscription_instance_ids"]

    def component_cls(self):
        return GetAgentStatusComponent

    def setUp(self) -> None:
        self.init_mock_client()
        mock.patch(gse_v2_mock_path, self.gse_mock_client).start()
        super().setUp()

    def cases(self):
        return [
            ComponentTestCase(
                name="查询Agent状态全部为RUNNING成功",
                inputs=self.common_inputs,
                parent_data={},
                execute_assertion=ExecuteAssertion(
                    success=True, outputs={"succeeded_subscription_instance_ids": self.fetch_succeeded_sub_inst_ids()}
                ),
                schedule_assertion=None,
                patchers=None,
            )
        ]
