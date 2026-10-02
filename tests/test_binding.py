import unittest
from publishing_qa.binding import binding_matches, select_producers, validate_bindings, validate_producers


class BindingTests(unittest.TestCase):
    def test_category_and_path_binding(self):
        finding = {"finding_id":"F-1","category":"code","file":"docs/nb/6502.md"}
        binding = {"match":{"category":"code","file":"docs/**/*.md"},"producers":["edu65xx-sim"]}
        self.assertTrue(binding_matches(binding, finding))
        self.assertEqual(select_producers(finding, [binding]), ["edu65xx-sim"])

    def test_unrelated_build_does_not_bind(self):
        finding = {"finding_id":"F-1","category":"fact","file":"docs/nb/cpu.md"}
        binding = {"match":{"category":"build"},"producers":["pdf-build"]}
        self.assertFalse(binding_matches(binding, finding))

    def test_specific_finding_binding(self):
        finding = {"finding_id":"OPENAI-0007","category":"fact"}
        binding = {"match":{"finding_id":"OPENAI-0007"},"producers":["datasheet-check"]}
        self.assertTrue(binding_matches(binding, finding))

    def test_unknown_producer_is_invalid(self):
        errors = validate_bindings(
            [{"match":{"category":"code"},"producers":["missing"]}],
            {"compiler"},
        )
        self.assertTrue(errors)

    def test_empty_match_is_invalid(self):
        self.assertTrue(validate_bindings([{"match":{},"producers":["compiler"]}], {"compiler"}))

    def test_valid_producer_polarity(self):
        self.assertEqual(validate_producers([{
            "id":"negative-test","type":"executable_test","command":"make negative-test",
            "supports_on_success":"dispute","supports_on_failure":"confirm","supports_on_timeout":"context",
        }]), [])

    def test_invalid_producer_polarity_is_rejected(self):
        errors = validate_producers([{
            "id":"tests","type":"executable_test","command":"make test",
            "supports_on_failure":"maybe",
        }])
        self.assertTrue(any("supports_on_failure" in error for error in errors))

    def test_duplicate_producer_ids_are_rejected(self):
        errors = validate_producers([
            {"id":"tests","type":"executable_test","command":"make test"},
            {"id":"tests","type":"compiler","command":"make compile"},
        ])
        self.assertTrue(any("duplicates producer id" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
