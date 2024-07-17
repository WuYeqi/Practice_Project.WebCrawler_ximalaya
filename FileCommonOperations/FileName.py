import re


# 合法化文件/文件夹名
# 去除 Windows 新建文件/文件夹不能包含的字符 (\/:*?<>|)
def legalized_file_name(album_title):
    invalid_chars = '[\\/:*?"<>|]'
    return re.sub(invalid_chars, "", album_title)


# 正则表达式 匹配文件后缀名
def regex_match_file_suffix(string):
    return re.search(r"\.(mp3|wav|wma|ogg|ape|acc|m4a)", string).group(0)
