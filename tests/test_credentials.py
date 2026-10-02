import unittest
from publishing_qa.providers.credentials import credential_for


class CredentialTests(unittest.TestCase):
    def test_reads_provider_key(self):
        self.assertEqual(credential_for("openai", {"OPENAI_API_KEY":"secret"}), "secret")

    def test_missing_key_fails_without_leaking_value(self):
        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
            credential_for("openai", {})


if __name__ == "__main__":
    unittest.main()
