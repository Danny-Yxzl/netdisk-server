# 这是私有工具包，存放加密算法等敏感信息


from textChecker import check as check_text  # 违规字符串检测


# 必须包括内容：加密和解密字符串算法（两者必须可互逆运算）
def encrypt_string(text):
    ans = ""
    for i in text:
        ans = ans + "%s-" % (ord(i) + 99)
    return ans[:-1]


def decode_string(text):
    try:
        text = text.split("-")
        ans = ""
        for i in text:
            ans = ans + chr(int(i) - 99)
        return ans
    except:
        return text
