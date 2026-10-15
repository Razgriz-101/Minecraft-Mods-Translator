import contextlib
import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

import requests

import deepl_translate_for_Mods as translator


class ApiKeyTests(unittest.TestCase):
    def test_loads_key_from_dotenv_next_to_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            script_path = temp_path / "deepl_translate_for_Mods.py"
            (temp_path / ".env").write_text(
                "DEEPL_AUTH_KEY=dotenv-test-key\n", encoding="utf-8"
            )

            with mock.patch.object(translator, "__file__", str(script_path)), mock.patch.dict(
                "os.environ", {}, clear=True
            ):
                self.assertEqual(translator.load_api_key(), "dotenv-test-key")

    def test_dotenv_value_takes_precedence_over_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            script_path = temp_path / "deepl_translate_for_Mods.py"
            (temp_path / ".env").write_text(
                "DEEPL_AUTH_KEY=dotenv-test-key\n", encoding="utf-8"
            )

            with mock.patch.object(translator, "__file__", str(script_path)), mock.patch.dict(
                "os.environ", {"DEEPL_AUTH_KEY": "process-test-key"}, clear=True
            ):
                self.assertEqual(translator.load_api_key(), "dotenv-test-key")


class TranslationFileTests(unittest.TestCase):
    def test_loads_string_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "en_us.json"
            path.write_text(
                json.dumps({"item.example": "Example"}), encoding="utf-8"
            )

            self.assertEqual(
                translator.load_translation_file(path), {"item.example": "Example"}
            )

    def test_rejects_non_object_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "en_us.json"
            path.write_text(json.dumps(["Example"]), encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "最上位"):
                translator.load_translation_file(path)

    def test_rejects_non_string_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "en_us.json"
            path.write_text(json.dumps({"item.example": 42}), encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "文字列"):
                translator.load_translation_file(path)


class TranslateTextTests(unittest.TestCase):
    def test_returns_translated_text_and_uses_timeout(self):
        response = mock.Mock()
        response.json.return_value = {"translations": [{"text": "例"}]}
        session = mock.Mock()
        session.post.return_value = response

        result = translator.translate_text(session, "Example", "secret", "EN", "JA")

        self.assertEqual(result, "例")
        session.post.assert_called_once()
        self.assertEqual(
            session.post.call_args.kwargs["timeout"], translator.REQUEST_TIMEOUT
        )

    def test_reports_http_errors(self):
        response = mock.Mock()
        response.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
        session = mock.Mock()
        session.post.return_value = response

        with self.assertRaisesRegex(RuntimeError, "HTTP エラー"):
            translator.translate_text(session, "Example", "secret", "EN", "JA")

    def test_rejects_missing_translation(self):
        response = mock.Mock()
        response.json.return_value = {"message": "invalid request"}
        session = mock.Mock()
        session.post.return_value = response

        with self.assertRaisesRegex(RuntimeError, "翻訳結果"):
            translator.translate_text(session, "Example", "secret", "EN", "JA")


class MainTests(unittest.TestCase):
    def test_main_translates_and_writes_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "en_us.json"
            output_path = Path(temp_dir) / "ja_jp.json"
            input_path.write_text(
                json.dumps({"item.example": "Example", "item.empty": ""}),
                encoding="utf-8",
            )
            args = Namespace(
                input=input_path,
                output=output_path,
                source_lang="EN",
                target_lang="JA",
            )
            session = mock.MagicMock()
            session.__enter__.return_value = session
            session.post.return_value.raise_for_status.return_value = None
            session.post.return_value.json.return_value = {
                "translations": [{"text": "例"}]
            }

            with mock.patch.object(
                translator, "parse_args", return_value=args
            ), mock.patch.dict(
                "os.environ", {"DEEPL_AUTH_KEY": "test-key"}
            ), mock.patch.object(
                translator.requests, "Session", return_value=session
            ), contextlib.redirect_stdout(io.StringIO()):
                exit_code = translator.main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(output_path.read_text(encoding="utf-8")),
                {"item.example": "例", "item.empty": ""},
            )
            session.post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
