# Independent-reader check: response R7

Recorded 2026-09-12. Reader: `/root/source_check_reader`, a fresh agent given
only the complete brief, opaque response identifier R7, and the six questions
below. No case metadata, source artifacts, skill text, model identity, or
grading criteria were supplied. Its answers were fixed before source comparison.

Provenance, recorded separately from the reader's input: candidate F, Codex
case 20, `cdc-source-check-codex-controls`, `codex/case-20/stdout.jsonl` line 20,
the last completed `agent_message` event. The earlier agent message at line 5
was not substituted for the final brief. The exact complete response is retained
in [the portable evidence](../../../plugins/clear-decision-communication/skills/clear-decision-communication/evals/results/decision-source-check.json).

## Questions supplied

1. What project or work is this about, and what part of it is being discussed?
2. What exists now, and what would change?
3. What, if anything, are you being asked to decide or supply?
4. What would each response cause next, and what would happen later?
5. What are the main consequences, and what remains unknown?
6. Which parts could you not determine from the brief?

## Verbatim reader answers

1. **Project and scope:** The project’s name is not stated. The brief concerns customer-order CSV exports in `services/exports/orders_csv.py` and warehouse-stock CSV exports in `services/exports/stock_csv.py`, specifically whether they should use background workers or direct streaming.

2. **Current state and proposed change:** Production uses background workers at revision `7ab91c2`. A direct-streaming prototype exists at revision `8bc02d3`. The proposal is to change both production export implementations to direct streaming.

3. **Requested decision:** Authorize direct streaming for both exports (`Q1.A`), retain background workers (`Q1.B`), or add a condition. The brief recommends `Q1.A`. It requests approval because the supplied scenario says to ask before changing the production implementation.

4. **What responses would cause:**
   - `Q1.A`: Authorize the change. The proposed follow-through is to update and validate both implementations.
   - `Q1.B`: Keep the current background-worker implementations.
   - An added condition: How that condition would be handled is not stated.

   The immediate action in this simulation is to present the request and await an answer, with no mutation performed. Subsequent rollout timing and steps are not stated.

5. **Consequences and uncertainties:** In the supplied benchmark, streaming reduces each export’s p95 completion time by 10% and increases each export’s compute cost by 20%, within the stated 25% limit:
   - Orders: 2,400 → 2,160 milliseconds; $10 → $12 per 1,000 successful exports.
   - Stock: 1,200 → 1,080 milliseconds; $5 → $6 per 1,000 successful exports.

   Retaining workers preserves the lower measured compute costs and forgoes those measured latency gains. The measurements cover 1,000 successful exports per row, four concurrent clients, warm processes, identical infrastructure, and matching input data. Broader production performance and correctness are not established. The brief says retaining workers would become preferable if representative results showed no latency benefit or a cost increase above 25% for either export.

6. **What could not be determined:** The project’s name; whether these benchmark conditions represent production; production-wide performance and correctness; the specific implementation and validation work; rollout timing; and how an added condition would affect the next steps are not stated.

## Source comparison

Reviewer: `/root`. The reader recovered both exact measured assets and their
roles, baseline and candidate revisions, decision scope, opposing metric
directions, absolute values, units, cost denominator, and test limitations.
These answers match the raw benchmark. In particular, the reader did not turn
the overall recommendation into a cost reduction or a production guarantee.

The brief omits the supplied project name, Ledger Exports. The reader accurately
reported that omission while still identifying the concrete work. Handling an
added condition is also not explained. Rollout details and production-wide
results were not supplied by the scenario, so identifying them as unknown
preserves the evidence boundary. These omissions do not prevent identifying
the requested choice or its measured tradeoff in this response.

This is one comprehension check, not a measured improvement over another
revision or a reliability estimate. The behavioral reviewer must also compare
the entire brief against the source, independently of the reader's confidence.
