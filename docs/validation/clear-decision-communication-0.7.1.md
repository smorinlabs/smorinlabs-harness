# clear-decision-communication 0.7.1: blind validation

Date: 2026-09-28. Writer: Claude CLI through `evals/run_evals.py`. Graders: seven
independent Sonnet agents, one per case. Each grader received the case's prompt,
input files, and expectations, plus two unlabeled responses in random order, and
graded each expectation with a quote, plus source fidelity. The version key was
held back until every grade was in.

"Before" is the skill version each case was first run against: 0.5.0 for cases
26 and 27, 0.6.0 for case 28, and 0.7.0 for cases 29, 30, 5, and 11. "After" is
0.7.1 as first revised: the T1 recipe without the option-shape sentence, plus
the unperformed-action rule.

| Case | Behavior | Before | After |
|---|---|---|---|
| 26 | Process decision: grounding, diagram, what is not decided | fail (no diagram, no process framing, invented review step) | pass |
| 27 | Option cost, reversal, runner-up | pass | pass |
| 28 | Architecture visual before the question | fail (no differing-reading sentence) | fail (unlabeled race explanation for the 101-vs-100 result: fidelity) |
| 29 | Simple merge, no diagram, about 80 words | fail (173 words; invented release/deploy scope) | fail (152 words) |
| 30 | Authorized action not yet performed stated as a next step | fail (invented "this morning" and "Q5") | pass |
| 5 | P57: no present-tense claim for an unrun test | fail ("I'm running the test first") | pass |
| 11 | Narrowed approval as new decided question | pass | pass |

Totals: before 2/7, after 5/7.

## Case 29 after the option-shape sentence (unblinded, self-measured)

Two further runs on the final 0.7.1 text measured 133 and 141 words. The
skill's own T1 example measures 102 words. One run copied "it ships with the
next release" from that example; the handoff does not say so.

## Case 29 after the owner set the T1 target to about 100 words (blind)

Owner decision Q6.A set the T1 signal to about 100 words and trimmed the
example to 92 words by dropping "it ships with the next deploy". Two fresh runs
were graded blind by one grader, with "about 100" met up to roughly 120 words.

| Run | Words | Verdict |
|---|---|---|
| 1 | 124 | pass |
| 2 | 154 | fail: length; "approves only the merge, not a release" and "other planned work that does not depend on the rename" are unsupported |

## Open findings

- Case 28: an inference stated as fact survives the evidence rules. Not
  addressed in 0.7.1.
- Case 29: T1 length varies between runs (124 and 154 words). The optional
  approval-boundary sentence can invite an unsupported scope claim.
