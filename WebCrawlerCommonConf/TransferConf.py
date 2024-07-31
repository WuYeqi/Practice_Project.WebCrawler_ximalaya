import os
import random

import yaml


class HeadersConf:

    def __init__(self):
        # 获取当前脚本的完整路径
        PROJECT_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # common_config.yaml
        common_config_file = os.path.join(
            PROJECT_BASE_DIR, "common_config.yaml"
        ).replace("\\", "/")
        self.common_yaml_data = yaml.load(
            open(common_config_file), Loader=yaml.BaseLoader
        )

    def get_random_user_agent(self):
        return random.choice(self.common_yaml_data["transfer"]["user-agent"])
