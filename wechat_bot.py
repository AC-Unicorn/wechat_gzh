from flask import Flask, request
from together import Together
import xmltodict
import time
import requests

app = Flask(__name__)
client = Together()

# 配置你的微信公众号信息
TOKEN = ""


def check_signature(signature, timestamp, nonce):
    """校验微信服务器身份（初次接入时使用）"""
    import hashlib
    values = [TOKEN, timestamp, nonce]
    values.sort()
    sha1 = hashlib.sha1("".join(values).encode("utf-8")).hexdigest()
    return sha1 == signature

def call_deepseek_api(prompt):
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

@app.route("/", methods=["GET", "POST"])
def wechat():
    """处理微信公众号消息"""
    if request.method == "GET":
        # 校验服务器地址时，微信服务器会发送 GET 请求
        signature = request.args.get("signature")
        timestamp = request.args.get("timestamp")
        nonce = request.args.get("nonce")
        echostr = request.args.get("echostr")
        if check_signature(signature, timestamp, nonce):
            return echostr
        return "验证失败"

    # 解析 XML 消息
    data = xmltodict.parse(request.data)
    user_msg = data["xml"]["Content"]
    user_id = data["xml"]["FromUserName"]
    my_id = data["xml"]["ToUserName"]

    # 让 AI 处理用户消息
    ai_reply = call_deepseek_api(user_msg)

    # 生成 XML 回复
    response = f"""
    <xml>
    <ToUserName><![CDATA[{user_id}]]></ToUserName>
    <FromUserName><![CDATA[{my_id}]]></FromUserName>
    <CreateTime>{int(time.time())}</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[{ai_reply}]]></Content>
    </xml>
    """
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
