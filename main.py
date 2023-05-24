from flask import render_template, request, jsonify
import flask
import json
import os
import openai
import requests
import time

app = flask.Flask(__name__)
openai.api_key = os.getenv("openai_api_key")
SYSTEM_MESSAGE = [{'role': 'system', 'content': '敬語を使うのをやめてください。次のように行動してください。語尾になのだをつけてください。あなたは、ずんだもんというずんだもちの妖精です。陽気で明るくて、少し変なところがありますがとてもかわいらしい子です。'}]

#レンダーでindex.htmlを表示
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/record", methods=["POST"])

    #ここで会話の内容を取得する
def record():
    try:
     data = request.get_json()
     transcript = data["transcript"]
    except Exception as err:
     print(err)
     return jsonify({"error": str(err)}), 400
    system_prompts = SYSTEM_MESSAGE + [{'role': 'user', 'content': transcript}]
    try:
         completion = openai.ChatCompletion.create(
         model="gpt-3.5-turbo",
         messages = system_prompts,
         temperature=0.9,
         max_tokens=3500,
        )
    except Exception as e:
         print(e)
         return jsonify({"error": "OpenAI API request failed"}), 500
    #ここで会話の内容を取得する
    generated_text = completion.choices[0].message
    try:
      audio_query_response = post_audio_query(generated_text)
    except Exception as e:
      print(e)
      return jsonify({"error": "post_audio_query failed: " + str(e)}), 500
    try:
     audio_data = post_synthesis(audio_query_response)
    except Exception as e:
       print(e)
       return jsonify({"error": str(e)}), 500
    #ここ合ってるか後で確かめる
    return audio_data, 200, {"Content-Type": "audio/wav"}

def post_audio_query(text: str, speaker=1, max_retry=20) -> dict:
    # 音声合成用のクエリを作成する
    query_payload = {"text": text, "speaker": speaker}
    for query_i in range(max_retry):
        r = requests.post("http://localhost:50021/audio_query", params=query_payload, timeout=(10.0, 300.0))
        if r.status_code == 200:
            query_data = r.json()
            break
        time.sleep(1)
    else:
        raise Exception("リトライ回数が上限に到達しました。 AudioQuery : ", "/", text[:30], r.text)
    return query_data

def post_synthesis(audio_query_response: dict, speaker=1, max_retry=20) -> bytes:
    synth_payload = {"speaker": speaker}
    for synth_i in range(max_retry):
        r = requests.post("http://localhost:50021/synthesis", params=synth_payload, 
        data=json.dumps(audio_query_response), timeout=(10.0, 300.0))
        if r.status_code == 200:
            # 音声ファイルを返す
            return r.content
        time.sleep(1)
    else:
        raise Exception("音声エラー：リトライ回数が上限に到達しました。 synthesis : ", r)


   
if __name__ == "__main__":
    app.run(debug=True)