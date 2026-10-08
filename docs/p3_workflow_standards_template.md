# Workflow standards (Alteryx)

1. **Naming:** `<area>_<purpose>_v<version>.yxmd`, e.g. `recon_positions_v1.yxmd`.
2. **Containers:** one Tool Container per stage, titled with a number: `1 Inputs`, `2 Clean`, `3 Data-quality gate`, `4 Reconcile`, `5 Outputs`.
3. **Annotations:** every tool has an annotation saying *why* it is there, not just what it is.
4. **No hard-coding:** file paths and thresholds come from `config/recon_config.csv` (or Interface tools).
5. **Never drop rows silently:** anything filtered out goes to an exceptions output with a reason.
6. **Errors:** a Test or Message tool stops the run if an input is empty or a key field is null.
7. **Outputs:** written to `output/` with the run date in the file name.
8. **Peer review:** a second person runs it from a clean copy before it is scheduled.
