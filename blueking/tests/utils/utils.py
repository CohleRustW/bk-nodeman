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


def get_user_model():
    try:
        from account.models import BkUser as User
    except Exception:
        from django.contrib.auth.models import User
    return User


def load_tests_settings():
    return {
        "valid_app": {
            "bk_app_code": "",
            "bk_app_secret": "",
        },
        "bk_user": {
            "bk_username": "admin",
            "bk_token": "",
        },
    }


tests_settings = load_tests_settings()
