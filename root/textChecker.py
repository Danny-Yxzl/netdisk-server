# coding=utf-8

from aliyunsdkcore import client
from aliyunsdkcore.profile import region_provider
from aliyunsdkgreen.request.v20180509 import TextScanRequest
import json
import uuid
import datetime


clt = ...   # AcessKey info
region_provider.modify_point("Green", "cn-shanghai", "green.cn-shanghai.aliyuncs.com")


def check(text):
    # 每次请求时需要新建request，请勿复用request对象。
    request = TextScanRequest.TextScanRequest()
    request.set_accept_format("JSON")
    task1 = {"dataId": str(uuid.uuid1()),
             "content": text,
             "time": datetime.datetime.now().microsecond
             }
    # 文本反垃圾检测场景的场景参数是antispam。
    request.set_content(bytearray(json.dumps({"tasks": [task1], "scenes": ["antispam"]}), "utf-8"))
    response = clt.do_action_with_exception(request)
    result = json.loads(response)
    return result["data"][0]["results"][0]["label"]


if __name__ == "__main__":
    print(check(text=input()))
