"""Bounded synthetic-only five-method/EXP05 profiling. Never opens HAI."""
from __future__ import annotations
import cProfile
import json
from pathlib import Path
import pstats
import tempfile
import time
import tracemalloc
import sys
from hashlib import sha256

from test_validation_v2_front_pipeline_v1 import synthetic_pipeline
from paperworks.validation_v2.front_execution_v1 import write_json_v1
from paperworks.validation_v2.gdn_sidecar_v1 import seal
from paperworks.validation_v2.isolation_forest_v1 import build_detector_environment_receipt_v1


def main():
    # Fixed sizes/repeats, not a search over scientific parameters.
    with tempfile.TemporaryDirectory() as directory:
        synthetic_pipeline(Path(directory),rows=2048,relations=2,per_relation=3)
    root_source=Path.cwd().resolve()
    files={Path(m.__file__).resolve() for n,m in list(sys.modules.items()) if n.startswith(("paperworks.","test_validation_v2_")) and getattr(m,"__file__",None)}
    files.add(Path(__file__).resolve())
    identities={str(p.relative_to(root_source)).replace("\\","/"):sha256(p.read_bytes()).hexdigest() for p in sorted(files) if p.is_relative_to(root_source)}
    records=[]
    for rows,per_relation in ((2048,10),(8192,40)):
        for repeat in range(2):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                profiler=cProfile.Profile()
                start=time.perf_counter();cpu_start=time.process_time()
                profiler.enable()
                result=synthetic_pipeline(root,rows=rows,relations=39,per_relation=per_relation)
                profiler.disable()
                cpu=time.process_time()-cpu_start;wall=time.perf_counter()-start
                stats=pstats.Stats(profiler)
                top=sorted(stats.stats.items(),key=lambda item:item[1][3],reverse=True)[:20]
                functions=[{"module":Path(key[0]).name,"function":key[2],"calls":value[1],"cumulative_seconds":value[3]} for key,value in top]
                files=[p for p in root.rglob("*") if p.is_file()]
                record={"synthetic_rows":rows,"rules":39,"opportunities":39*per_relation,"repeat":repeat,
                    "wall_seconds":wall,"cpu_seconds":cpu,"cpu_one_core_percent":100*cpu/wall,
                    "python_allocator_peak_bytes":"NOT_MEASURED_FINAL_CPU_PROFILE","process_rss_peak":"NOT_MEASURED",
                    "persisted_file_count":len(files),"persisted_file_bytes":sum(p.stat().st_size for p in files),
                    "os_disk_io":"NOT_MEASURED","rows_per_second":rows/wall,"traces_per_second":39*per_relation/wall,
                    "gpu":"NOT_APPLICABLE_CPU_DETECTORS_AND_PYTHON_RUNTIME","top_functions":functions,
                    "five_method_bundle_pass":True,"full_trace_census_pass":result["trace_receipt"]["unit_count"]==39*per_relation}
                records.append(record)
                print(json.dumps({"stage":"SYNTHETIC_PREFLIGHT","rows":rows,"opportunities":39*per_relation,"repeat":repeat,"wall_seconds":round(wall,3)}),flush=True)
    if any(sha256((root_source/path).read_bytes()).hexdigest()!=digest for path,digest in identities.items()):raise ValueError("PROFILE_SOURCE_CHANGED")
    write_json_v1(Path("research_control_center/validation_v2/performance_preflight/EXP04_05_PROFILE_RESULTS_V2.json"),seal({
        "schema":"exp04_05_synthetic_profile_v1","records":records,"environment":build_detector_environment_receipt_v1().to_document(),
        "loaded_source_hashes":identities,"loaded_sources_unchanged_during_profile":True,"gdn_sidecar_annotation_included":True,
        "warmup_runs":1,"data":"SYNTHETIC_ONLY","scientific_config_changes":0,"test1_accesses":0,"test2_accesses":0,"label_file_accesses":0,
        "measurement_caveat":"cProfile timings; no tracemalloc in final profile. Earlier V1 allocation profile is a pre-hardening snapshot, not final-code equivalence. Persisted bytes are not OS disk throughput."}))


if __name__=="__main__":main()
