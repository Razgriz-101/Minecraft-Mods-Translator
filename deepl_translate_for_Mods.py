import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


DEEPL_TRANSLATE_URL = "https://api-free.deepl.com/v2/translate"
REQUEST_TIMEOUT = (10, 60)


def load_api_key():
    env_path = Path(__file__).resolve().with_name(".env")
    load_dotenv(dotenv_path=env_path, override=True)
    return os.environ.get("DEEPL_AUTH_KEY")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Minecraft の言語 JSON ファイルを DeepL API で翻訳します。"
    )
    parser.add_argument("input", type=Path, help="翻訳元の en_us.json")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("ja_jp.json"),
        help="翻訳先ファイル (既定: ./ja_jp.json)",
    )
    parser.add_argument(
        "--source-lang", default="EN", help="翻訳元言語コード (既定: EN)"
    )
    parser.add_argument(
        "--target-lang", default="JA", help="翻訳先言語コード (既定: JA)"
    )
    return parser.parse_args()


def load_translation_file(path):
    try:
        with path.open("r", encoding="utf-8") as source_file:
            data = json.load(source_file)
    except OSError as exc:
        raise RuntimeError(f"入力ファイルを開けません: {path} ({exc})") from exc
    except UnicodeError as exc:
        raise RuntimeError(f"入力ファイルは UTF-8 形式である必要があります: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"入力ファイルの JSON を読み取れません: {path} ({exc})"
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError("入力 JSON の最上位はオブジェクトである必要があります。")

    invalid_keys = [key for key, value in data.items() if not isinstance(value, str)]
    if invalid_keys:
        examples = ", ".join(repr(key) for key in invalid_keys[:5])
        suffix = " ほか" if len(invalid_keys) > 5 else ""
        raise RuntimeError(
            f"翻訳対象の値はすべて文字列である必要があります。対象キー: {examples}{suffix}"
        )

    return data


def translate_text(session, text, api_key, source_lang, target_lang):
    response = session.post(
        DEEPL_TRANSLATE_URL,
        headers={"Authorization": f"DeepL-Auth-Key {api_key}"},
        data={
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
        },
        timeout=REQUEST_TIMEOUT,
    )

    try:
        response.raise_for_status()
    except requests.RequestException as exc:
        response_body = getattr(exc.response, "text", "").strip()
        if response_body:
            response_body = f" 応答: {response_body[:500]}"
        raise RuntimeError(
            f"DeepL API が HTTP エラーを返しました: {exc}{response_body}"
        ) from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError("DeepL API の応答を JSON として読み取れません。") from exc

    if not isinstance(result, dict):
        raise RuntimeError("DeepL API の応答形式が正しくありません。")

    translations = result.get("translations")
    if not isinstance(translations, list) or not translations:
        raise RuntimeError("DeepL API の応答に翻訳結果がありません。")

    translated_text = (
        translations[0].get("text") if isinstance(translations[0], dict) else None
    )
    if not isinstance(translated_text, str):
        raise RuntimeError("DeepL API の応答に有効な翻訳テキストがありません。")

    return translated_text


def main():
    args = parse_args()
    api_key = load_api_key()
    if not api_key:
        print(
            "エラー: スクリプトと同じフォルダーの .env に "
            "DEEPL_AUTH_KEY を設定してください。",
            file=sys.stderr,
        )
        return 2

    input_path = args.input.expanduser()
    output_path = args.output.expanduser()

    try:
        if os.path.normcase(input_path.resolve()) == os.path.normcase(output_path.resolve()):
            print(
                "エラー: 入力ファイルと出力ファイルには別のパスを指定してください。",
                file=sys.stderr,
            )
            return 2

        source_data = load_translation_file(input_path)
        total_chars = sum(len(value) for value in source_data.values())
        translated_data = {}

        with requests.Session() as session:
            for count, (key, value) in enumerate(source_data.items(), start=1):
                translated_data[key] = (
                    translate_text(
                        session,
                        value,
                        api_key,
                        args.source_lang,
                        args.target_lang,
                    )
                    if value
                    else ""
                )
                print(f"進捗：{count} / {len(source_data)}")

        with output_path.open("w", encoding="utf-8") as target_file:
            json.dump(translated_data, target_file, indent="\t", ensure_ascii=False)

    except (OSError, requests.RequestException, RuntimeError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    print(f"翻訳文字数：{total_chars}")
    print(f"出力ファイル：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
