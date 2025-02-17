from flask import Flask, request, jsonify
from together import Together
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
        file_path = f"{MEDIA_SAVE_PATH}/{media_id}.amr"
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"语音文件已下载: {file_path}")
        return file_path
    else:
        print("语音下载失败:", response.json())
        return None

def call_deepseek_api(prompt):
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

@app.route("/wechat", methods=["POST"])
def wechat():
    """处理微信公众号消息，并返回 JSON 响应"""
    try:
        data = request.get_json()
        msg_type = data.get("MsgType", "")
        user_id = data.get("FromUserName", "")
        
        if msg_type == "text":
            user_msg = data.get("Content", "")
        elif msg_type == "voice":
            user_msg = data.get("Recognition", "")
            media_id = data.get("MediaId", "")
            if not user_msg:
                audio_file = download_voice(media_id)
                user_msg = audio_to_text(audio_file)
        else:
            return jsonify({"error": "暂不支持该类型消息"})

        ai_reply = call_deepseek_api(user_msg)
        
        return jsonify({
            "user_id": user_id,
            "message": user_msg,
            "reply": ai_reply,
            "timestamp": int(time.time())
        })

    except Exception as e:
        print(f"Error processing WeChat request: {e}")
        return jsonify({"error": "处理失败", "details": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
