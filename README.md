# Minecraft Mods Translator

Minecraft mod の英語言語ファイル（`en_us.json`）を DeepL API で日本語に翻訳し、`ja_jp.json` として保存する Python スクリプトです。

## 必要なもの

- Python 3
- DeepL API の認証キー
- 翻訳する `en_us.json`

## セットアップ

依存パッケージをインストールします。

```powershell
python -m pip install -r requirements.txt
```

リポジトリのルートに `.env` を作成し、DeepL API の認証キーを設定します。`.env.example` をコピーしてキーを書き換えてください。

```powershell
Copy-Item .env.example .env
```

`.env` の内容:

```dotenv
DEEPL_AUTH_KEY=your-deepl-api-key
```

`.env` はGit管理から除外されています。認証キーをソースコードや公開リポジトリに保存しないでください。

## 入力形式

翻訳キーをキー、翻訳対象を文字列の値とする JSON オブジェクトを用意します。

```json
{
  "item.example.name": "Example Item",
  "item.example.description": "A sample item."
}
```

## 実行

入力ファイルのパスを指定して実行します。既定では、実行時の作業ディレクトリに `ja_jp.json` を作成します。

```powershell
python .\deepl_translate_for_Mods.py "C:\path\to\en_us.json"
```

出力先を変更する場合は `--output` を指定します。

```powershell
python .\deepl_translate_for_Mods.py "C:\path\to\en_us.json" --output "C:\path\to\ja_jp.json"
```

翻訳元・翻訳先の言語コードは `--source-lang` と `--target-lang` で変更できます。既定値は `EN` から `JA` です。

```powershell
python .\deepl_translate_for_Mods.py .\en_us.json --source-lang EN --target-lang JA
```

同名の出力ファイルは上書きされます。入力ファイルと出力ファイルに同じパスは指定できません。

## 動作と制約

- 入力 JSON の最上位はオブジェクト、各値は文字列である必要があります。形式が異なる場合は API を呼び出す前にエラーを表示します。
- 空文字列は API に送らず、空文字列のまま出力します。
- 空文字列以外の各値を個別に DeepL API へ送信します。進捗と入力文字数をコンソールに表示します。
- 通信にはタイムアウトを設定しています。HTTPエラー、通信エラー、DeepL の不正な応答があればエラーを表示して終了します。
- 自動再試行や途中経過の保存は行いません。翻訳がすべて成功した後に出力ファイルを書き込みます。
- API の利用量や料金は、利用する DeepL アカウントの契約内容を確認してください。

## テスト

ユニットテストはモックを使うため、DeepL API キーやネットワーク接続なしで実行できます。

```powershell
python -m unittest discover -s tests -v
```
