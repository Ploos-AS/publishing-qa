import unittest
from publishing_qa.judge import judge_record


class JudgeTests(unittest.TestCase):
    def test_unverified_fact_needs_human_review_even_with_four_votes(self):
        consensus = {"consensus_id":"CON-1","finding_ids":["a","b","c","d"],"agreement_count":4,"requires_verification":True}
        findings = {x:{"severity":"high","verification_status":"unverified"} for x in "abcd"}
        result = judge_record(consensus, findings)
        self.assertEqual(result["disposition"], "needs_human_review")

    def test_non_verification_finding_can_be_likely(self):
        consensus = {"consensus_id":"CON-1","finding_ids":["a"],"agreement_count":1,"requires_verification":False}
        result = judge_record(consensus, {"a":{"severity":"medium","verification_status":"unverified"}})
        self.assertEqual(result["disposition"], "likely")


if __name__ == "__main__":
    unittest.main()
