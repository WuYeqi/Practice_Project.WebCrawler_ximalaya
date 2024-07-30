import cv2


class Slider:

    def __init__(self):
        self.top_side = 0
        self.bottom_side = 0
        self.slide_img_cut_offset = 0

        self.slide_img_initial_width = 0
        self.bg_img_initial_width = 0

    def crop_slide(self, slide_img):
        # 参考：https://blog.csdn.net/lly1122334/article/details/108083052
        ## 裁去透明底的拼图滑块的不规则部分，仅保留中心的矩形图案用于识别
        cv2_slide_img = slide_img["cv2"]
        height, self.slide_img_initial_width, channel = cv2_slide_img.shape
        assert channel == 4  # 无透明通道报错

        first_transparency = []
        last_transparency = []
        for y, rows in enumerate(cv2_slide_img):
            # 扫描每一行

            # 单行内扫描
            first_location = None  # 最左侧非透明点
            last_location = None  # 最右侧非透明点
            for x, RGBA in enumerate(rows):
                alpha = RGBA[3]

                # 该像素非透明
                if alpha:
                    if not first_location:
                        # 更新最左侧非透明点坐标
                        first_location = (x, y)
                        first_transparency.append(first_location)

                    # 更新最右侧非透明点坐标
                    last_location = (x, y)

            if last_location:
                last_transparency.append(last_location)

        first_transparency_sorted_x = sorted(first_transparency, key=(lambda x: x[0]))
        # 裁去上方突起
        index = 0
        while first_transparency[index][1] < first_transparency_sorted_x[0][1]:
            first_transparency.pop(index)
            last_transparency.pop(index)
            index += 1

        self.top_side = first_transparency_sorted_x[0][1]
        left_side = first_transparency_sorted_x[-1][0]
        self.bottom_side = first_transparency[-1][1]
        rigth_side = last_transparency[-1][0]

        self.slide_img_cut_offset = first_transparency_sorted_x[-1][0]

        # 裁去左右突起，保留中心矩形的图案
        return cv2_slide_img[self.top_side : self.bottom_side, left_side:rigth_side]

    def crop_bg_by_slide(self, bg_img):
        cv2_bg_img = bg_img["cv2"]
        self.bg_img_initial_width = bg_img["initial_width"]

        # 裁剪验证码图片
        return cv2_bg_img[
            self.top_side : self.bottom_side, 0 : self.bg_img_initial_width
        ]

    def get_drag_distance(self, bg_img, slide_img):

        ## 裁去透明底的拼图滑块的不规则部分，仅保留中心的矩形图案用于识别
        cv2_slide_img_crop = self.crop_slide(slide_img)

        ## 并根据滑块裁剪结果，裁剪验证码图片，仅保留对应区域，缩小搜索范围
        cv2_bg_img_crop = self.crop_bg_by_slide(bg_img)

        min_val, max_val, min_loc, max_loc = self.match(
            cv2_bg_img_crop, cv2_slide_img_crop
        )

        return max_loc[0] - self.slide_img_cut_offset

    def match(self, bg_img, slide_img):
        slide_img = cv2.cvtColor(slide_img, cv2.COLOR_BGRA2BGR)

        # 执行模板匹配，采用的匹配方式cv2.TM_SQDIFF_NORMED
        result = cv2.matchTemplate(bg_img, slide_img, cv2.TM_CCORR)
        # 归一化处理
        cv2.normalize(result, result, 0, 1, cv2.NORM_MINMAX, -1)

        return cv2.minMaxLoc(result)

    def calibrate(self, img_drag_distance, params):
        # 按钮实际可滑动总长（滑轨总长 - 滑轨按钮直径）
        slider_activity_distance = (
            params["slide_rail_distance"] - params["slide_btn_diameter"]
        )

        # 画面可滑动总长（验证码图初始宽度 - 滑块图初始宽度 + 滑块图固有偏差）
        img_slide_distance = (
            self.bg_img_initial_width
            - self.slide_img_initial_width
            + params["fixed_offset"]
        )

        # 实际滑动距离
        img_drag_distance += params["fixed_offset"]
        return img_drag_distance / img_slide_distance * slider_activity_distance
