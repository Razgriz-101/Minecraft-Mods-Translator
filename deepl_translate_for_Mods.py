import json
import requests

API_KEY = "YOUR_DEEPL_API_KEY"  # DeepL API key
SOURCE_LANG = 'EN'  # 翻訳元言語
TARGET_LANG = 'JA'  # 翻訳先言語

tl_vol = 0
value_len = 0
temp_tld_dict = {}

path = r"C:\Users\********\en_us.json"  # jsonファイルのパスを指定
with open(path, 'r', encoding="utf-8") as src_f:  # jsonファイルを開く
    src_load = json.load(src_f)  # jsonファイルの内容を「json_load」に代入（dict型）

for key, value in src_load.items():
    temp_tld_dict[key] = value
    value_len += len(src_load[key])  # DeepL APIの無料版は1ヶ月当たりの翻訳文字数に制限があるためカウントする

    params = {
        'auth_key': API_KEY,
        'text': src_load[key],
        'source_lang': SOURCE_LANG,
        'target_lang': TARGET_LANG
    }

    request = requests.post("https://api-free.deepl.com/v2/translate", data=params)
    result = request.json()  # 翻訳された文字列を受け取る
    print(result)  # {'translations': [{'detected_source_language': 'EN', 'text': '翻訳文'}]}
    temp_tld_dict[key] = result['translations'][0]['text']

    tl_vol += 1
    print('進捗：' + str(tl_vol) + ' / ' + str(len(src_load)))  # 例）進捗：84 / 115

with open('ja_jp.json', 'wt', encoding="utf-8") as tgt_f:
    json.dump(temp_tld_dict, tgt_f, indent='\t', ensure_ascii=False)  # UTF-8の日本語で書き出し

print('翻訳文字数：' + str(value_len))  # 例）翻訳文字数：2643
