import os
import random


from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import yaml

from .TransferConf import HeadersConf


class WebdriverOptionsConf:
    def __init__(self):
        headers_conf = HeadersConf()

        self.options = webdriver.ChromeOptions()
        self.options.add_argument(
            "--user-agent=%s" % headers_conf.get_random_user_agent()
        )
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])

        self.options.set_capability("pageLoadStrategy", "none")

    def get_options(self):
        return self.options
