import os
import unittest
from unittest.mock import patch

from app.config import Settings


class SettingsModelAliasTests(unittest.TestCase):
    def test_openai_model_defaults_to_approved_terra_selection(self) -> None:
        self.assertEqual(Settings(_env_file=None).openai_model, "gpt-5.6-terra")

    def test_model_is_a_legacy_alias_for_openai_model(self) -> None:
        with patch.dict(
            os.environ,
            {"MODEL": "gpt-test-model", "GEMINI_MODEL": "gemini-test-model"},
            clear=True,
        ):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.openai_model, "gpt-test-model")
        self.assertEqual(settings.gemini_model, "gemini-test-model")

    def test_openai_model_takes_priority_when_both_names_exist(self) -> None:
        with patch.dict(
            os.environ,
            {"OPENAI_MODEL": "gpt-preferred", "MODEL": "gpt-legacy"},
            clear=True,
        ):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.openai_model, "gpt-preferred")

    def test_field_name_still_works_for_programmatic_settings(self) -> None:
        settings = Settings(_env_file=None, openai_model="gpt-programmatic")
        self.assertEqual(settings.openai_model, "gpt-programmatic")


if __name__ == "__main__":
    unittest.main()
