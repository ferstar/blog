# Tensor unlock and quantized MoE: numeric evidence

These files accompany the draft article `tensor-unlock-quantized-moe`.

- [requests.csv](requests.csv): 121 completed request rows, split into 82 unlocked and 39 stock-rate observations.
- [summary.json](summary.json): native token/time sums, derived rates, environment, and measurement limits.
- [verify.py](verify.py): standard-library-only offline recomputation and manifest verification.
- [SHA256SUMS](SHA256SUMS): SHA-256 of the other files, excluding the manifest itself.

Keep the files together and run:

```sh
python3 verify.py
```

These are two different natural workloads on the same Strata 0.1.48 engine and configuration. They are not matched-input benchmark trials. Task content, context lengths, prefix reuse, and speculative-draft acceptance differ. No causal unlock speedup is claimed.

The CSV is a selected numeric subset of archived `/metrics?requests=all` responses. Per-request totals reconciled with the original server aggregates before export. Original IDs were replaced by per-batch sequence numbers, and prompt bodies, model outputs, precise request timestamps, machine paths, hardware identifiers, and authentication material were omitted. The exported fields and removal policy are recorded in `summary.json`.

Every exported row finished with `stop`, and API output tokens match native generated tokens. One active request at the stock snapshot was excluded. The unlocked window retains a recovery acceptance check. Reasoning tokens count as generated tokens when thinking is enabled.

The GPU was an RTX 4090 D with 24 GB of VRAM and a 425 W power cap, using NVIDIA 615.78.08 open modules and kernel 7.3.0-ros2go-btf. State readback was 0/0/0 for unlocked and 1/1/1 for stock in the affected rate fields. The model was Qwen3.8-Flash-Next IQ3_S with 7681 expert-cache slots. See `summary.json` for the remaining reproducibility metadata.
