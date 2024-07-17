import argparse
import json
import os
import random
import re
import sys
import time


from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import requests
import yaml


sys.path.append("..")
from sources_rewritten.getSoundCryptLink import JSReverse
from WebCrawlerCommonConf.WebdriverConf import WebdriverOptionsConf
from WebCrawlerCommonConf.TransferConf import HeadersConf
from FileCommonOperations.FileName import *


import http.cookiejar as HC


class WebCrawler_ximalaya:

    def __init__(self):
        driver_conf = WebdriverOptionsConf()
        options = driver_conf.get_options()
        self.driver = webdriver.Chrome(options=options)

        # 获取当前脚本的完整路径
        PROJECT_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(PROJECT_BASE_DIR, "config.yaml").replace("\\", "/")

        # config.yaml
        yaml_data = yaml.load(open(config_file), Loader=yaml.BaseLoader)

        ## 文件下载保存路径
        self.save_dir = yaml_data["basic"]["save_dir"]

        ## 预存的headers
        self.headers = yaml_data["transfer"]["headers"]
        self.headers["User-Agent"] = HeadersConf().get_random_user_agent()

        # cookies.txt
        self.cookies_file = os.path.join(PROJECT_BASE_DIR, "cookies.txt").replace(
            "\\", "/"
        )

        # 相关接口
        self.base_url = yaml_data["basic"]["base_url"]
        self.api_tracks_list = yaml_data["basic"]["api_tracks_list"]
        self.api_tracks_info = yaml_data["basic"]["api_tracks_info"]

        # 运行时传入参数 --id=[专辑id]
        parser = argparse.ArgumentParser()
        parser.add_argument("--id", type=int)
        self.args = parser.parse_args()

    def download_album(self):
        driver = self.driver
        album_id = str(self.args.id)
        url = self.base_url + album_id

        driver.get(url)
        # Webdriver添加cookies 自动登录
        with open(self.cookies_file, "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.refresh()
        # 为requests 获取cookies
        cookie_list = [
            item["name"] + "=" + item["value"] for item in driver.get_cookies()
        ]
        cookies = {"Cookie": ";".join(item for item in cookie_list)}

        load_waiting = WebDriverWait(driver, 30)
        XPATH_sound_list = "//div[@class='sound-list  H_g']"
        load_waiting.until(EC.presence_of_element_located((By.XPATH, XPATH_sound_list)))

        # 专辑标题 albumTitle
        soup = BeautifulSoup(driver.page_source, features="lxml")
        album_title = soup.find("h1", attrs={"class": "title z_i"}).contents[0]
        album_title = legalized_file_name(album_title)
        print(
            time.strftime("%H:%M:%S", time.localtime()),
            "  即将下载专辑：",
            album_title,
            "\n",
            url,
        )

        is_download_continue = True
        pageNum = 1  # 当前页码

        session = requests.Session()

        while is_download_continue:

            # api_tracks_list: https://www.ximalaya.com/revision/album/v1/getTracksList/
            params = {"albumId": album_id, "pageNum": pageNum, "sort": 0}
            response = session.get(
                self.api_tracks_list, params=params, headers=self.headers
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

                params = {
                    "device": "www2",
                    "trackId": track["trackId"],
                    "trackQualityLevel": 1,
                }
                timestamp = int(time.time() * 1000)
                response = requests.get(
                    self.api_tracks_info + str(timestamp),
                    params=params,
                    headers=self.headers,
                    cookies=cookies,
                )
                playUrlList = (
                    json.loads(response.text).get("trackInfo").get("playUrlList")[0]
                )

                track_url = JSReverse.get_sound_crypt_link(playUrlList["url"])

                # 下载文件
                file_type = regex_match_file_suffix(track_url)
                save_dir = os.path.join(self.save_dir, album_title)
                file_save_name = track_index + "_" + track_title + file_type
                try:
                    if not os.path.exists(save_dir):
                        os.mkdir(save_dir)
                except FileNotFoundError as e:
                    print("文件下载保存路径异常，请检查设置")

                file_path = os.path.join(save_dir, file_save_name)
                response = requests.get(
                    track_url,
                    headers=self.headers,
                    cookies=cookies,
                )
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

        driver.close()


WebCrawler_ximalaya().download_album()
