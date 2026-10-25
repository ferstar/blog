"""Recalculate the published measurements; no network or GPU access."""
from pathlib import Path
import csv
import hashlib
import json
import math
import re
import statistics

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def main():
    expected_names = set()
    for line in (ROOT / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert re.fullmatch(r'[0-9a-f]{64}', digest), name
        assert Path(name).name == name and name not in expected_names, name
        expected_names.add(name)
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    actual_names = {p.name for p in ROOT.iterdir() if p.is_file() and p.name != 'SHA256SUMS'}
    assert actual_names == expected_names, (actual_names ^ expected_names)
    print(f'Integrity: {len(expected_names)} file hashes matched')

    gemm = {}
    for stage in ['before', 'after']:
        text = (ROOT / f'gemm-{stage}.log').read_text()
        summaries = {k: float(v) for k, v in re.findall(r'^(\w+) median_TFLOPS=([\d.]+)', text, re.M)}
        assert set(summaries) == {'FP16_FP32', 'BF16_FP32', 'TF32', 'FP32_control'}
        for mode, recorded in summaries.items():
            values = [float(x) for x in re.findall(r'^' + re.escape(mode) + r' sample=\d+ TFLOPS=([\d.]+)', text, re.M)]
            assert len(values) == 5 and math.isclose(statistics.median(values), recorded, abs_tol=1e-9)
        gemm[stage] = summaries
    print('GEMM (median TFLOPS, 5 samples x 20 iterations):')
    for mode in gemm['before']:
        before, after = gemm['before'][mode], gemm['after'][mode]
        print(f'  {mode}: {before:.2f} -> {after:.2f}, {(after / before - 1) * 100:+.2f}%')

    for stage in ['before', 'after']:
        numeric = (ROOT / f'numeric-{stage}.log').read_text()
        assert numeric.count('65536 cells, failures=0, max_abs=0') == 2
        tensor = load(f'tensor-modes-{stage}.log')
        for mode in ['f16_f32', 'tf32', 'u4_s32']:
            result = tensor['modes'][mode]
            assert result['cells_checked'] == 270336 and result['mismatches'] == 0
    rates = load('rates.json')
    for stage, obj in rates.items():
        expected = 1 if stage == 'before' else 0
        assert all(obj['rates'][k] == expected for k in ['fmla32', 'imla2', 'imla4'])
    print('Correctness and rate checks: passed for the archived test cases')

    runs = load('inference-runs.json')
    assert len(runs) == 15 and len({(r['case'], r['rep']) for r in runs}) == 15
    with (ROOT / 'inference-runs.csv').open(newline='') as stream:
        csv_rows = list(csv.DictReader(stream))
    assert len(csv_rows) == len(runs)
    for row, flat in zip(runs, csv_rows):
        assert row['http_status'] == 200 and row['sse_done'] and row['finish_reason'] == 'length'
        assert row['usage']['completion_tokens'] == row['timings']['predicted_n'] == row['server_request']['engine_generated'] == row['requested_output_tokens']
        assert row['usage']['prompt_tokens_details']['cached_tokens'] == row['timings']['cache_n'] == 0
        assert row['timings']['prompt_n'] == row['usage']['prompt_tokens']
        assert row['request_counter_delta'] == 1 and row['reasoning_characters'] == 0
        assert row['wall_s'] >= row['ttft_s'] > 0
        assert flat['case'] == row['case'] and int(flat['rep']) == row['rep']
        numeric_fields = {
            'prompt_tokens': row['usage']['prompt_tokens'],
            'completion_tokens': row['usage']['completion_tokens'],
            'cached_tokens': row['timings']['cache_n'],
            'prefill_tok_s': row['timings']['prompt_per_second'],
            'decode_tok_s': row['timings']['predicted_per_second'],
            'ttft_s': row['ttft_s'], 'wall_s': row['wall_s'],
        }
        assert all(float(flat[key]) == value for key, value in numeric_fields.items())
    stored = load('inference-summary.json')
    print('Inference (3 requests/case; tokens, prefill tok/s, decode tok/s, TTFT s, total s):')
    for case in ['short', '2k', '8k', 'sustained', '32k-code']:
        rows = [r for r in runs if r['case'] == case]
        assert len(rows) == 3 and {r['rep'] for r in rows} == {1, 2, 3}
        prompt_tokens = sorted({r['usage']['prompt_tokens'] for r in rows})
        outputs = {r['usage']['completion_tokens'] for r in rows}
        assert len(prompt_tokens) == len(outputs) == 1
        computed = {
            'samples': 3, 'prompt_tokens': prompt_tokens, 'output_tokens': next(iter(outputs)),
            'prefill_tok_s_median': statistics.median(r['timings']['prompt_per_second'] for r in rows),
            'decode_tok_s_median': statistics.median(r['timings']['predicted_per_second'] for r in rows),
            'ttft_s_median': statistics.median(r['ttft_s'] for r in rows),
            'wall_s_median': statistics.median(r['wall_s'] for r in rows),
            'decode_tok_s_range': [min(r['timings']['predicted_per_second'] for r in rows), max(r['timings']['predicted_per_second'] for r in rows)],
            'prefill_tok_s_range': [min(r['timings']['prompt_per_second'] for r in rows), max(r['timings']['prompt_per_second'] for r in rows)],
        }
        assert computed == stored[case], case
        print(f"  {case}: {prompt_tokens[0]}/{computed['output_tokens']}, {computed['prefill_tok_s_median']:.1f}, {computed['decode_tok_s_median']:.1f}, {computed['ttft_s_median']:.3f}, {computed['wall_s_median']:.3f}")
    print('15 formal requests verified; one warmup excluded. No model quality check or controlled inference unlock A/B.')


if __name__ == '__main__':
    main()
