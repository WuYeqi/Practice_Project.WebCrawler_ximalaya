import os
import sys

import yaml

sys.path.append("..")
from WebCrawlerCommonConf.TransferConf import HeadersConf


class YamlData:

    def __init__(self):
        # 获取当前脚本的完整路径
        PROJECT_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(PROJECT_BASE_DIR, "config.yaml").replace("\\", "/")

        # config.yaml
        with open(config_file, encoding="utf-8") as f:
            yaml_data = yaml.load(f, Loader=yaml.BaseLoader)

        ## 文件下载保存路径
        self.save_dir = yaml_data["basic"]["save_dir"]
        self.account = {
            "accountName": yaml_data["basic"]["account"]["accountName"],
            "accountPWD": yaml_data["basic"]["account"]["accountPWD"],
        }

        ## 预存的headers
        self.headers = yaml_data["transfer"]["headers"]
        self.headers["User-Agent"] = HeadersConf().get_random_user_agent()

        # 相关接口
        self.album_url = yaml_data["transfer"]["URL"]["base_album_url"]
        self.api_tracks_list = yaml_data["transfer"]["URL"]["api_tracks_list"]
        self.api_tracks_info = yaml_data["transfer"]["URL"]["api_tracks_info"]
