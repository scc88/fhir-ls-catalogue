import sys, json, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import *
import part1_core, part2_specs, part3_process_data, part4_docs_bundles
S = Source(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "source", "sakura-bloom-r2-extract.json"))
part1_core.build(S)
part2_specs.build(S)
part3_process_data.build(S)
finalize()
OUT = os.environ.get('OUT', os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fhir"))
SUMMARY = part4_docs_bundles.build(S, OUT)
json.dump({'issues': ISSUES, 'bundles': SUMMARY}, open(OUT + '/../build-log.json', 'w'), indent=1, ensure_ascii=False)
from collections import Counter
print(Counter(k.split('/')[0] for k in R))
print(len(ISSUES), "issues")
for i in ISSUES: print(" -", i[:160])
