# Startup Meeting Quality Audit Addendum

This addendum records the final interpretive decisions used to clear the startup corpus for downstream analysis.

## Noise-handling rule

Opening noise and closing noise should be **disregarded** when they clearly reflect recording continuation before the meeting begins or after the meeting has already ended. These segments are not to be interpreted as evidence of transcript corruption or analytic unreliability.

## Meeting-specific clarifications

| meeting_id | Clarification | Operational consequence |
| --- | --- | --- |
| `2024.10.14startup_b` | The final segment after the main interaction appears to be **closing noise** from a machine that remained recording after the meeting ended. The lines beginning around 5521s–6044s should not be treated as substantive meeting content. | Keep the meeting in the corpus and disregard the terminal segment as post-meeting noise. |
| `2025.03.31startup_a` | The large initial gap reflects **opening noise** and a transition from non-meeting audio into participant entry, not a recording failure. | Keep the meeting in the corpus and disregard the opening segment as pre-meeting noise. |
| `2025.04.14startup_a` | The final delayed segment is **closing noise / shutdown noise** following meeting completion. | Keep the meeting in the corpus and disregard the terminal segment as post-meeting noise. |

## Expanded anonymization rule

Recurring genuine entities and obvious orthographic variants from the affected meetings should be treated as **anonymizable** whenever they identify people, organizations, brands, departments, locations, investors, partners, or clients in a way that is unnecessary for downstream analysis.

The currently recognized examples include names such as `Paulo Moraes`, `Paulo Morais`, and `Ivan`, and entities such as `LinkedIn`, `Instagram`, `Quatro Rodas`, `Tecnogera`, `Joy Venturi`, `JV`, `Ultragaz`, `Mercado Livre`, and `Max Park`.

## Final implication for Step 2

Under these clarified rules, the remaining flagged cases do not represent substantive structural failures. The retained startup corpus can therefore proceed to **Step 2 across all 34 meetings** without substantive caveats.
