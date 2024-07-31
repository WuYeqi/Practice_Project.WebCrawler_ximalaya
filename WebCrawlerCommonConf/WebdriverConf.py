from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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

    def add_proxy_server(self):
        self.options.add_argument("--proxy-server=socks5://127.0.0.1:10808")

    def get_driver(self, chromedriver_path, add_proxy_server=False):
        if add_proxy_server:
            self.add_proxy_server()

        service = Service(executable_path=chromedriver_path)
        self.driver = webdriver.Chrome(options=self.options, service=service)
        return self.driver

    def waiting_until(self, locator):
        delay = 60
        WebDriverWait(self.driver, delay).until(EC.presence_of_element_located(locator))
