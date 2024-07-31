import argparse
import json
import os
import sys
import time


from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import cv2
import requests.cookies
import requests


sys.path.append("..")
from CrackCaptcha.PuzzleSlider import Slider
from FileCommonOperations.FileName import *
from sources_rewritten.getSoundCryptLink import JSReverse
from WebCrawlerCommonConf.WebdriverConf import WebdriverOptionsConf
from YamlDataConf import YamlData


class WebCrawler_ximalaya:

    def __init__(self):

        # 获取当前脚本的完整路径
        PROJECT_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # cookies.txt
        self.cookies_file = os.path.join(PROJECT_BASE_DIR, "cookies.txt").replace(
            "\\", "/"
        )

        # 临时文件夹
        self.tmp_dir = os.path.join(PROJECT_BASE_DIR, "tmp_dir").replace("\\", "/")
        if not self.tmp_dir:
            os.makedirs(self.tmp_dir)

        # 运行时传入参数 --id=[专辑id]
        parser = argparse.ArgumentParser()
        parser.add_argument("--id", type=int)
        self.args = parser.parse_args()

        self.WDOC = WebdriverOptionsConf()
        chromedriver_path = r"C:\Users\QiQi\AppData\Local\Programs\Python\Python312\Scripts\chromedriver.exe"
        self.driver = self.WDOC.get_driver(chromedriver_path)

    def download_album(self):
        yaml_data = YamlData()
        driver = self.driver

        album_id = str(self.args.id)
        url = yaml_data.album_url + album_id

        driver.get(url)
        driver.maximize_window()
        with open(self.cookies_file, "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)

        driver.refresh()

        # 悬停右上角头像，判断登陆状态
        time.sleep(1)
        actions = ActionChains(driver)
        locator = (By.XPATH, '//*[@id="rootHeader"]/div/div[2]/div')
        self.WDOC.waiting_until(locator)
        element = driver.find_element(By.XPATH, '//*[@id="rootHeader"]/div/div[2]/div')
        actions.move_to_element(element).perform()

        # cookies已过期，账号未登录
        try:
            driver.find_element(By.XPATH, '//div[contains(text(),"个人页")]')
        except NoSuchElementException as e:
            self.auto_login()

        # requests 从文件中获取cookies
        cookies_dict = {}
        with open(self.cookies_file, "r") as f:
            cookies = json.load(f)
            for item in cookies:
                cookies_dict[item["name"]] = item["value"]

        # 开始下载
        XPATH_sound_list = "//div[@class='sound-list  H_g']"
        self.WDOC.waiting_until((By.XPATH, XPATH_sound_list))

        session = requests.Session()
        # 专辑标题 albumTitle
        soup = BeautifulSoup(driver.page_source, features="lxml")
        driver.close()

        album_title = soup.find("h1", attrs={"class": "title z_i"}).contents[0]
        album_title = legalized_file_name(album_title)
        print(
            time.strftime("%H:%M:%S", time.localtime()),
            "  即将下载专辑：",
            album_title,
            " -- ",
            url,
        )

        is_download_continue = True
        pageNum = 1  # 当前页码

        while is_download_continue:

            # api_tracks_list: https://www.ximalaya.com/revision/album/v1/getTracksList/
            params = {"albumId": album_id, "pageNum": pageNum, "sort": 0}
            response = session.get(
                yaml_data.api_tracks_list,
                params=params,
                headers=yaml_data.headers,
                cookies=cookies_dict,
            )

            # 专辑音频总数
            trackTotalCount = json.loads(response.text).get("data")["trackTotalCount"]

            # 当前页音频数据列表
            response_tracks = json.loads(response.text).get("data").get("tracks")
            if not response_tracks:
                is_download_continue = False
                break

            for track in response_tracks:
                # 处理单个音频数据
                track_index = str(track["index"]).zfill(len(str(trackTotalCount)))
                track_title = legalized_file_name(track["title"])

                # 反爬 - 修改请求头 headers中的 Referer 字段
                yaml_data.headers["Host"] = "www.ximalaya.com"
                yaml_data.headers["Referer"] = "https://www.ximalaya.com/sound/" + str(
                    track["trackId"]
                )

                params = {
                    "device": "www2",
                    "trackId": track["trackId"],
                    "trackQualityLevel": 1,
                }
                timestamp = int(time.time() * 1000)
                url = yaml_data.api_tracks_info + str(timestamp)
                response = session.get(url, params=params, headers=yaml_data.headers)

                playUrlList = (
                    json.loads(response.text).get("trackInfo").get("playUrlList")[0]
                )

                track_url = JSReverse.get_sound_crypt_link(playUrlList["url"])

                # 下载文件
                file_type = regex_match_file_suffix(track_url)
                save_dir = os.path.join(yaml_data.save_dir, album_title)
                file_save_name = track_index + "_" + track_title + file_type
                try:
                    if not os.path.exists(save_dir):
                        os.mkdir(save_dir)
                except FileNotFoundError as e:
                    print("文件下载保存路径异常，稍后请检查设置")

                file_path = os.path.join(save_dir, file_save_name)

                # 迷惑，get加了headers反而会403Forbidden
                response = session.get(track_url)
                if response.headers.get("Content-Length") < 500:
                    print("收到数据大小 < 500字节，疑似为无效资源，请确认!!")
                else:
                    with open(file_path, "wb") as f:
                        print(
                            time.strftime("%H:%M:%S", time.localtime()),
                            "  (当前进度：",
                            track_index,
                            "/",
                            trackTotalCount,
                            ")" "  当前下载文件",
                            file_save_name,
                        )
                        print(" ———— url：", track_url)
                        f.write(response.content)

            pageNum += 1

    def auto_login(self):
        yaml_data = YamlData()
        driver = self.driver
        driver.find_element(By.XPATH, '//div[contains(text(),"账号")]').click()

        driver.find_element(By.XPATH, '//div[@class="login-tab-btn"]').click()

        input_accountName = driver.find_element(By.XPATH, '//input[@id="accountName"]')
        input_accountPWD = driver.find_element(By.XPATH, '//input[@id="accountPWD"]')
        login_btn = driver.find_element(By.XPATH, '//button[@class="login-btn"]')

        input_accountName.send_keys(yaml_data.account["accountName"])
        input_accountPWD.send_keys(yaml_data.account["accountPWD"])
        login_btn.click()

        # 突破概率出现的拼图滑块验证码
        time.sleep(1)
        captcha_xpath = '//div[@class="mmv-panel WU_"]'
        try:
            while driver.find_element(By.XPATH, captcha_xpath):

                locator = (By.XPATH, '//div[@class="__xmca-block"]')
                self.WDOC.waiting_until(locator)
                slide_block = driver.find_element(
                    By.XPATH, '//div[@class="__xmca-block"]'
                )

                bg_img_xpath = '//img[@class="__xmca-img-main"]'
                slide_img_xpath = '//img[@class="__xmca-img-bl"]'
                # 获取验证码图片资源
                bg_img, slide_img = self.get_captcha_img_resources(
                    bg_img_xpath, slide_img_xpath
                )

                slider = Slider()
                img_drag_distance = slider.get_drag_distance(bg_img, slide_img)

                # 模拟鼠标拖动
                calibrate_params = {
                    # 误差校准
                    "slide_rail_distance": 378.67,  # 滑轨总长
                    "slide_btn_diameter": 38,  # 滑轨按钮直径
                    "fixed_offset": 0.35294117647059053,  # 拼图固有偏差
                }
                actions = ActionChains(driver)
                actions.click_and_hold(slide_block).perform()
                actions.move_by_offset(
                    slider.calibrate(img_drag_distance, calibrate_params), 0
                ).release().perform()

                os.remove(bg_img["path"])
                os.remove(slide_img["path"])

                time.sleep(1)
        except NoSuchElementException as e:
            pass

        cookies = json.dumps(driver.get_cookies())
        # 更新本地cookies json文件
        with open(self.cookies_file, "w") as f:
            f.write(cookies)

    # 获取验证码图片资源
    def get_captcha_img_resources(self, bg_img_xpath, slide_img_xpath):
        driver = self.driver

        pattern = "[^/]+(?!.*/)"
        # 获取验证码背景大图
        bg_img_src = driver.find_element(By.XPATH, bg_img_xpath).get_attribute("src")
        bg_img_name = re.search(pattern, bg_img_src).group(0)
        bg_img_name = self.tmp_dir + "/" + bg_img_name

        bg_img = requests.get(bg_img_src)
        with open(bg_img_name, "wb") as f:
            f.write(bg_img.content)

        # 获取验证码滑块小图
        slide_img_src = driver.find_element(By.XPATH, slide_img_xpath).get_attribute(
            "src"
        )
        slide_img_name = re.search(pattern, slide_img_src).group(0)
        slide_img_name = self.tmp_dir + "/" + slide_img_name

        slide_img = requests.get(slide_img_src)
        with open(slide_img_name, "wb") as f:
            f.write(slide_img.content)

        bg_img = cv2.imread(bg_img_name)
        slide_img = cv2.imread(slide_img_name, cv2.IMREAD_UNCHANGED)

        bg_img = {
            "cv2": bg_img,
            "path": bg_img_name,
            "initial_height": bg_img.shape[0],
            "initial_width": bg_img.shape[1],
        }
        slide_img = {
            "cv2": slide_img,
            "path": slide_img_name,
            "initial_height": slide_img.shape[0],
            "initial_width": slide_img.shape[1],
        }
        return bg_img, slide_img


WebCrawler_ximalaya().download_album()
