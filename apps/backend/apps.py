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


from django.apps import AppConfig


class BackendConfig(AppConfig):
    name = "apps.backend"
    verbose_name = "Backend"

    def ready(self):
        from apps.backend.plugin.signals import activity_failed_handler
        from pipeline.engine.signals import activity_failed

        activity_failed.connect(activity_failed_handler, dispatch_uid="_activity_failed")
