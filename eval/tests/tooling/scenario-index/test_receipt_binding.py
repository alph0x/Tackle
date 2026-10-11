import hashlib, json, os, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
SCENARIO=ROOT/"eval/scenarios/s75-write-boundary"
META=ROOT/"eval/tests/tooling/scenario-index/measurement-binding.json"
RECEIPT_SHA="9b4ebc6137da753ba91a87e9205fbf2bc73b3e51ed2f23a3a696f2386989b67e"
VALIDATOR_SHA="2ebc2197fc165502e1bd1c5c22dbc174445ab21ec7202754365f81a728ae9998"
def sha(data):
    return hashlib.sha256(data).hexdigest()
def mapping_digest(mapping):
    raw=json.dumps(mapping,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return sha(raw)
def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))
class ReceiptBoundScenarioIndex(unittest.TestCase):
    def test_s75_variants_match_public_projection(self):
        meta=load_json(META)
        self.assertEqual(meta["schema"],"tackle-measurement-binding/1")
        self.assertEqual(meta["receipt_sha256"],RECEIPT_SHA)
        self.assertEqual(meta["validator_sha256"],VALIDATOR_SHA)
        index=load_json(ROOT/"eval/scenarios/INDEX.json")
        entry=next(x for x in index["scenarios"] if x["scenario_id"]=="s75-write-boundary")
        variants={x["variant_id"]:x for x in entry["variants"]}
        self.assertEqual(set(variants),{"v1","h1","v3","h3"})
        for name,split in (("v3","development"),("h3","held-out")):
            recorded=meta["variants"][name];variant=variants[name]
            projection=recorded["scenario_projection"]
            self.assertEqual(recorded["split"],split)
            self.assertEqual(variant["split"],split)
            self.assertEqual(variant["path"],projection["path"])
            self.assertEqual(variant["prompts"],["task.md"])
            self.assertEqual(variant["fixture"],"fixture")
            self.assertTrue(variant["stageable"])
            self.assertEqual(variant["fixture_sha256"],projection["fixture_sha256"])
            projected=ROOT/projection["path"]
            mapping={p.relative_to(projected).as_posix():sha(p.read_bytes())
                     for p in sorted(projected.rglob("*")) if p.is_file()}
            self.assertEqual(list(mapping.values()),projection["input_file_hashes"])
            self.assertEqual(mapping_digest(mapping),projection["fixture_sha256"])
            self.assertIn("task.md",mapping)
            self.assertTrue(any(key.startswith("fixture/") for key in mapping))
    def test_scenario_consumer_calls_pinned_validator_when_bound(self):
        receipt=os.environ.get("MEASUREMENT_RECEIPT_PATH")
        validator=os.environ.get("MEASUREMENT_VALIDATOR_PATH")
        bindings=os.environ.get("MEASUREMENT_BINDINGS_PATH")
        meta=load_json(META)
        if not (receipt and validator and bindings):
            self.assertEqual(meta["receipt_sha256"],RECEIPT_SHA)
            self.assertEqual(meta["validator_sha256"],VALIDATOR_SHA)
            return
        receipt_path=Path(receipt);validator_path=Path(validator);binding_path=Path(bindings)
        self.assertEqual(sha(receipt_path.read_bytes()),RECEIPT_SHA)
        self.assertEqual(sha(validator_path.read_bytes()),VALIDATOR_SHA)
        sys.path.insert(0,str(validator_path.parent))
        import author_boundary
        frozen=load_json(receipt_path)
        current=author_boundary.verify_frozen(ROOT,frozen)
        bound=load_json(binding_path)["bindings"]
        author_boundary.verify_consumer_bindings(frozen,bound)
        with self.assertRaises(ValueError):
            author_boundary.verify_consumer_bindings(frozen,{"native_runner":bound["native_runner"]})
        for variant in ("v3","h3"):
            source_map=frozen["fixture_packages"][variant]["fixture_sources"]
            author_boundary.verify_staging_sources(frozen,variant,source_map)
            projection=meta["variants"][variant]["scenario_projection"]
            expected={"task.md":frozen["fixture_packages"][variant]["prompt"],
                **{"fixture/"+key:value for key,value in source_map.items()}}
            for relative,source in expected.items():
                self.assertEqual((ROOT/projection["path"]/relative).read_bytes(),(ROOT/source).read_bytes())
            damaged=dict(source_map);damaged["unreceipted.txt"]="docs/unreceipted.txt"
            with self.assertRaises(ValueError):
                author_boundary.verify_staging_sources(frozen,variant,damaged)
            self.assertEqual(set(current["input_manifest"][variant]["subject_inputs"]),set(frozen["input_manifest"][variant]["subject_inputs"]))
            self.assertEqual(set(current["input_manifest"][variant]["rubrics"]),set(frozen["input_manifest"][variant]["rubrics"]))
