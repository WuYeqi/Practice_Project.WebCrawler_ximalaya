import base64
import numpy
import os
import re


import yaml


class JSReverse:

    def get_sound_crypt_link(encrypted_link):

        decode_link_t = encrypted_link

        # 获取常量数据
        PROJECT_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        const_data_file = os.path.join(PROJECT_BASE_DIR, "const_data.yaml").replace(
            "\\", "/"
        )
        const_yaml_data = yaml.load(open(const_data_file), Loader=yaml.BaseLoader)
        uint8array_c = numpy.array(const_yaml_data["CONST_ARRAY_A"]).astype(numpy.uint8)
        uint8array_u = numpy.array(const_yaml_data["CONST_ARRAY_O"]).astype(numpy.uint8)

        decode_link_t = decode_link_t.replace("_", "/").replace("-", "+")
        decode_link_t = re.sub(re.compile(r"/[^A-Za-z0-9\+\/]/g"), "", decode_link_t)
        atob_e = base64.b64decode(decode_link_t + "===").decode("latin-1")

        if not atob_e or len(atob_e) < 16:
            return decode_link_t

        r = [0 for _ in range(len(atob_e) - 16)]
        uint8array_r = numpy.array(r).astype(numpy.uint8)
        for i in range(len(uint8array_r)):
            uint8array_r[i] = ord(atob_e[i])

        n = [0 for _ in range(16)]
        uint8array_n = numpy.array(n).astype(numpy.uint8)
        for i in range(len(uint8array_n)):
            uint8array_n[i] = ord(atob_e[len(atob_e) - 16 + i])

        for i in range(len(uint8array_r)):
            uint8array_r[i] = uint8array_u[uint8array_r[i]]

        for i in range(0, len(uint8array_r), 16):
            JSReverse.function_p(uint8array_r, i, uint8array_n)

        for i in range(0, len(uint8array_r), 32):
            JSReverse.function_p(uint8array_r, i, uint8array_c)

        uint8array_e = uint8array_r
        decode_link_t = ""
        i = 0
        while i < len(uint8array_e):
            term = uint8array_e[i].astype(numpy.int_)
            i += 1

            match term >> 4:
                case 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7:
                    character = chr(term)
                    decode_link_t += character
                    continue

                case 12 | 13:
                    a = uint8array_e[i]
                    i += 1
                    character = chr((31 & term) << 6 | 63 & a)
                    decode_link_t += character
                    continue

                case 14:
                    a = uint8array_e[i]
                    i += 1
                    b = uint8array_e[i]
                    i += 1
                    character = chr((15 & term) << 12 | (63 & a) << 6 | (63 & b) << 0)
                    decode_link_t += character

        return decode_link_t

    @staticmethod
    def function_p(front, index, later):
        for i in range(min(len(front) - index, len(later))):
            item = numpy.bitwise_xor(front[index + i], later[i])
            if type(item) is numpy.ndarray:
                front[index + i] = item[0]
            else:
                front[index + i] = item
