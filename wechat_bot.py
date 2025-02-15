from flask import Flask, request
from together import Together
import xmltodict
import time
import requests

from speech_to_text import audio_to_text

app = Flask(__name__)
client = Together()

# 配置你的微信公众号信息
TOKEN = ""
WECHAT_ACCESS_TOKEN = ""
MEDIA_SAVE_PATH = "wechat_audio"

def download_voice(media_id):
    """下载微信语音文件"""
    url = f"https://api.weixin.qq.com/cgi-bin/media/get?access_token={WECHAT_ACCESS_TOKEN}&media_id={media_id}"
    response = requests.get(url, stream=True)

    if response.status_code == 200:
        file_path = f"{MEDIA_SAVE_PATH}/{media_id}.amr"  # 语音文件格式可能是 amr 或 mp3
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"语音文件已下载: {file_path}")
        return file_path
    else:
        print("语音下载失败:", response.json())
        return None

def check_signature(signature, timestamp, nonce):
    """校验微信服务器身份（初次接入时使用）"""
    import hashlib
    values = [TOKEN, timestamp, nonce]
    values.sort()
    sha1 = hashlib.sha1("".join(values).encode("utf-8")).hexdigest()
    return sha1 == signature

def call_deepseek_api(prompt):
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

@app.route("/", methods=["GET", "POST"])
def wechat():
    """处理微信公众号消息，包括文本和语音"""
    if request.method == "GET":
        # 校验服务器地址
        signature = request.args.get("signature")
        timestamp = request.args.get("timestamp")
        nonce = request.args.get("nonce")
        echostr = request.args.get("echostr")
        if check_signature(signature, timestamp, nonce):
            return echostr
        print('Failed validation')
        return "验证失败"

    try:
        # 解析 XML 消息
        data = xmltodict.parse(request.data)
        msg_type = data["xml"].get("MsgType", "")
        user_id = data["xml"].get("FromUserName", "")
        my_id = data["xml"].get("ToUserName", "")
        
        if msg_type == "text":
            # 处理文本消息
            user_msg = data["xml"].get("Content", "")
        elif msg_type == "voice":
            # 处理语音消息
            user_msg = data["xml"].get("Recognition", "")  # 语音识别文本
            media_id = data["xml"].get("MediaId", "")
            if not user_msg:
                audio_file = download_voice(media_id)
                user_msg = audio_to_text(audio_file)
        else:
            return "暂不支持该类型消息"

        print(user_msg)
        # 让 AI 处理用户消息
        ai_reply = call_deepseek_api(user_msg)
        print(ai_reply)
        # 生成 XML 回复
        response_xml = f"""
        <xml>
        <ToUserName><![CDATA[{user_id}]]></ToUserName>
        <FromUserName><![CDATA[{my_id}]]></FromUserName>
        <CreateTime>{int(time.time())}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{ai_reply}]]></Content>
        </xml>
        """

        print('send resp...')
        return response_xml

    except Exception as e:
        print(f"Error processing WeChat request: {e}")
        return "处理失败"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
