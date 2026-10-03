import unittest
from pathlib import Path

import publishing_qa


class PackageDataTests(unittest.TestCase):
    def test_runtime_schemas_exist_in_package(self):
        root=Path(publishing_qa.__file__).resolve().parent/"schemas"
        required={
          "deterministic-report.schema.json",
          "review-run.schema.json",
          "provider-qualification.schema.json",
          "evidence-map.schema.json",
          "pipeline-report.schema.json",
          "finding.schema.json",
          "config.schema.json",
        }
        self.assertTrue(root.is_dir())
        self.assertEqual(required,{p.name for p in root.glob("*.json")})

    def test_release_runtime_schemas_match_public_copies(self):
        package_root=Path(publishing_qa.__file__).resolve().parent/"schemas"
        repo_root=Path(__file__).resolve().parents[1]
        names={
          "config.schema.json",
          "deterministic-report.schema.json",
          "review-run.schema.json",
          "provider-qualification.schema.json",
          "evidence-map.schema.json",
          "pipeline-report.schema.json",
          "finding.schema.json",
        }
        for name in names:
            self.assertEqual(
                (package_root/name).read_text(encoding="utf-8"),
                (repo_root/"schema"/name).read_text(encoding="utf-8"),
                name,
            )


if __name__=="__main__":
    unittest.main()
