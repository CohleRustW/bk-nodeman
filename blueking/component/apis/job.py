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
from ..base import ComponentAPI


class CollectionsJOB(object):
    """Collections of JOB APIS"""

    def __init__(self, client):
        self.client = client

        self.execute_job = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/job/execute_job/", description="启动作业"
        )
        self.fast_execute_sql = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/job/fast_execute_sql/",
            description="快速执行SQL脚本",
        )
        self.get_cron_list = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/job/get_cron_list/",
            description="查询业务下定时作业信息",
        )
        self.get_job_detail = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/job/get_job_detail/",
            description="查询作业模板详情",
        )
        self.get_job_instance_log = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/job/get_job_instance_log/",
            description="根据作业实例ID查询作业执行日志",
        )
        self.get_job_instance_status = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/job/get_job_instance_status/",
            description="查询作业执行状态",
        )
        self.get_job_list = ComponentAPI(
            client=self.client, method="GET", path="/api/c/compapi{bk_api_ver}/job/get_job_list/", description="查询作业模板"
        )
        self.get_os_account = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/job/get_os_account/",
            description="查询业务下的执行账号",
        )
        self.get_own_db_account_list = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/job/get_own_db_account_list/",
            description="查询用户有权限的DB帐号列表",
        )
        self.get_script_detail = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/job/get_script_detail/",
            description="查询脚本详情",
        )
        self.get_script_list = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/job/get_script_list/",
            description="查询脚本列表",
        )
        self.get_step_instance_status = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/job/get_step_instance_status/",
            description="查询作业步骤的执行状态",
        )
        self.update_cron_status = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/job/update_cron_status/",
            description="更新定时作业状态",
        )
        self.fast_execute_script = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/job/fast_execute_script/",
            description="快速执行脚本",
        )
        self.fast_push_file = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/job/fast_push_file/",
            description="快速分发文件",
        )
        self.save_cron = ComponentAPI(
            client=self.client, method="POST", path="/api/c/compapi{bk_api_ver}/job/save_cron/", description="新建或保存定时作业"
        )
        self.change_cron_status = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/job/change_cron_status/",
            description="更新定时作业状态",
        )
        self.execute_task = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/job/execute_task/",
            description="根据作业模板ID启动作业",
        )
        self.execute_task_ext = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/job/execute_task_ext/",
            description="启动作业Ext(带全局变量启动)",
        )
        self.get_agent_status = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/job/get_agent_status/",
            description="查询Agent状态",
        )
        self.get_cron = ComponentAPI(
            client=self.client, method="GET", path="/api/c/compapi{bk_api_ver}/job/get_cron/", description="查询业务下定时作业信息"
        )
        self.get_task = ComponentAPI(
            client=self.client, method="GET", path="/api/c/compapi{bk_api_ver}/job/get_task/", description="查询作业模板"
        )
        self.get_task_detail = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/job/get_task_detail/",
            description="查询作业模板详情",
        )
        self.get_task_ip_log = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/job/get_task_ip_log/",
            description="根据作业实例ID查询作业执行日志",
        )
        self.get_task_result = ComponentAPI(
            client=self.client,
            method="GET",
            path="/api/c/compapi{bk_api_ver}/job/get_task_result/",
            description="根据作业实例 ID 查询作业执行状态",
        )
        self.execute_platform_job = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/job/execute_platform_job/",
            description=u"执行内置任务",
        )
        self.push_config_file = ComponentAPI(
            client=self.client,
            method="POST",
            path="/api/c/compapi{bk_api_ver}/job/push_config_file/",
            description=u"下发配置文件",
        )
        self.gse_proc_operate_v3 = ComponentAPI(
            client=self.client, method="POST", path="/component/compapi/job/gse_proc_operate_v3/", description=u"取消进程托管"
        )
