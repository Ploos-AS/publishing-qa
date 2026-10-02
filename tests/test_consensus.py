import unittest

from publishing_qa.consensus import apply_verification, summarize_groups


def f(fid, reviewer, problem, category="fact", file="docs/01.md", verify=True):
    return {
        "finding_id": fid, "reviewer": reviewer, "problem": problem,
        "claim": None, "category": category, "file": file,
        "severity": "high", "requires_verification": verify,
    }


class ConsensusTests(unittest.TestCase):
    def test_similar_findings_are_grouped(self):
        result = summarize_groups([
            f("A-1","a","Reset vector address appears incorrect"),
            f("B-1","b","The reset vector address is incorrect"),
        ])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["agreement_count"], 2)

    def test_agreement_does_not_confirm(self):
        result = summarize_groups([
            f("A-1","a","Reset vector address appears incorrect"),
            f("B-1","b","The reset vector address is incorrect"),
            f("C-1","c","Reset vector address seems incorrect"),
            f("D-1","d","Reset vector address is incorrect"),
        ])
        self.assertEqual(result[0]["agreement_count"], 4)
        self.assertEqual(result[0]["verification_status"], "unverified")

    def test_verification_requires_explicit_step(self):
        item = summarize_groups([f("A-1","a","Claim is wrong")])[0]
        verified = apply_verification(item, "confirmed", [{"type":"primary_source","ref":"datasheet"}])
        self.assertEqual(verified["verification_status"], "confirmed")
        self.assertEqual(len(verified["evidence"]), 1)

    def test_different_categories_do_not_merge(self):
        result = summarize_groups([
            f("A-1","a","Example is confusing","pedagogy",verify=False),
            f("B-1","b","Example is confusing","code"),
        ])
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
