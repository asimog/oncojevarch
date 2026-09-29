# T22 — Reconcile A001-A020 lessons

Status: COMPLETE
Dependencies: T02, T20
Verdict: KEEP — record durable architecture lessons (not biological claims) from recorded
results, in `docs/CONCEPT_BOOK.md` ("Earned lessons") so future agents inherit them.

## Lessons to record (one line each, verified against SCAFFOLD_MANIFEST/exec-plans)

1. question-specific deterministic projections beat giant context (A003/A004);
2. irrelevant state can cost or degrade semantic performance (A004);
3. use cheapest scientifically sufficient representations (A005);
4. deterministic high-recall retrieval precedes semantic reranking (A006);
5. Jev cannot rescue candidates eliminated upstream (A006 mechanics);
6. relative selection does not imply absolute adequacy (A007);
7. uncertainty-preserving search can beat irreversible greedy pruning (A008);
8. exploration has legitimate scientific value (A009);
9. rejected-candidate audits reveal search false negatives (A010);
10. null controls are necessary for semantic components (A011);
11. model upgrades need contract-specific regression evaluation (A013);
12. semantic feature discovery can overfit (A014 negative);
13. gap routing / no self-promotion works and is testable (A015);
14. bounded context must earn its value (A016 negative);
15. durable idempotent operations matter (A017);
16. architecture changes should be bounded and evidence-traceable (A018);
17. cheap representations can be scientifically insufficient (A019 negative);
18. the tested Jev→OncoX cascade did not establish savings (A012 negative);
19. A020 did not demonstrate a combined-arm frontier shift on recorded tasks;
20. negative results narrow architecture rather than cause arbitrary redesign.

## Acceptance

- Each lesson traces to a recorded result (exec-plans/completed or SCAFFOLD_MANIFEST).
- No lesson becomes a biological claim.

## Verification

`python scripts/verify.py`; cross-check each line against `docs/exec-plans/completed/`.
