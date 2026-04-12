# Step 05 calibration classification report

This report documents the approved 20-case calibration run for Step 05. Each case was classified from a transcript window centered on the Entropy-UCL peak (`peak_second ± 180 s`), with the transcript kept in its source language (Brazilian Portuguese) and all output labels and justifications standardized in English. Classifications were produced by Claude (claude-sonnet-4-6) applying the approved CP/FR codebook directly. The previous calibration artifacts in this folder were technical failures (HTTP 401 — invalid OpenAI API key) and have been replaced by this run.

## Calibration sample coverage

| Requirement | Target | Achieved |
|---|---:|---:|
| Sample size | 20 | 20 |
| Distinct meetings | 5 | 18 |
| Include meetings | 3 | 12 |
| Include-with-caution meetings | 2 | 6 |
| Joint corroborated = True | 8 | 10 |
| Joint corroborated = False | 8 | 10 |
| Middle or late events | 6 | 12 |
| Max cases from one meeting | 2 | 2 |

## Trigger-type distribution

| trigger_type | n | % |
|---|---:|---:|
| cognitive_perturbation | 11 | 55.0% |
| functional_reorientation | 9 | 45.0% |

Across the approved calibration set, `cognitive_perturbation` accounts for 11 cases (55.0%), whereas `functional_reorientation` accounts for 9 cases (45.0%). The CP-majority split is consistent with the Entropy-UCL detection logic: events were selected precisely because communication became unusually varied and complex, a signature more typical of frame-disrupting episodes than of routine coordination.

## Trigger-subtype distribution

| trigger_subtype | n | % |
|---|---:|---:|
| CP_generative | 7 | 35.0% |
| FR_elaboration | 6 | 30.0% |
| CP_constraint | 3 | 15.0% |
| FR_procedural | 2 | 10.0% |
| CP_divergence | 1 | 5.0% |
| FR_attention | 1 | 5.0% |

CP_generative is the most common subtype (7 cases), reflecting the early-stage nature of these startup teams, where high-entropy moments frequently coincide with the introduction of new possibilities, contacts, and market insights. CP_constraint (3) captures moments where new limitations enter the team's frame. FR_elaboration (6) is the most common FR subtype, reflecting moments of detailed plan development and synthesis.

## SMM-dimension distribution

| smm_dimension | n | % |
|---|---:|---:|
| smm_strategy | 11 | 55.0% |
| smm_task | 6 | 30.0% |
| smm_goals | 2 | 10.0% |
| smm_constraints | 1 | 5.0% |

## Confidence distribution

| confidence | n | % |
|---|---:|---:|
| conf_medium | 14 | 70.0% |
| conf_high | 6 | 30.0% |

No `conf_low` cases were produced. All windows had sufficient turn density (minimum 17 turns; mean ~38 turns) for reliable classification. This suggests the Entropy-UCL event detection is selecting informationally dense windows.

## Trigger type by joint corroboration

| joint_corroborated | cognitive_perturbation | functional_reorientation | total |
|---|---:|---:|---:|
| False | 6 | 4 | 10 |
| True | 5 | 5 | 10 |

## Trigger type by meeting quality

| quality_label | cognitive_perturbation | functional_reorientation | total |
|---|---:|---:|---:|
| include | 7 | 5 | 12 |
| include_with_caution | 4 | 4 | 8 |

## Case-level classifications

| calibration_case_id | meeting_id | peak_second | timing_bin | joint_corroborated | trigger_type | trigger_subtype | smm_dimension | confidence |
|---|---|---:|---|---|---|---|---|---|
| cal_01 | 2024.10.14startup_a | 2169 | middle | False | functional_reorientation | FR_elaboration | smm_strategy | conf_medium |
| cal_02 | 2024.10.25startup_a | 4115 | late | False | cognitive_perturbation | CP_divergence | smm_strategy | conf_high |
| cal_03 | 2024.10.28startup_b | 2143 | middle | True | cognitive_perturbation | CP_generative | smm_task | conf_medium |
| cal_04 | 2024.11.04startup_a | 2067 | middle | True | cognitive_perturbation | CP_generative | smm_strategy | conf_high |
| cal_05 | 2024.11.04startup_b | 2954 | middle | True | functional_reorientation | FR_elaboration | smm_task | conf_medium |
| cal_06 | 2024.11.11startup_a | 650 | early | False | cognitive_perturbation | CP_generative | smm_strategy | conf_high |
| cal_07 | 2024.11.11startup_b | 2732 | middle | True | cognitive_perturbation | CP_constraint | smm_constraints | conf_medium |
| cal_08 | 2024.11.18startup_a | 714 | early | True | functional_reorientation | FR_procedural | smm_strategy | conf_medium |
| cal_09 | 2024.11.18startup_b | 321 | early | True | cognitive_perturbation | CP_constraint | smm_strategy | conf_medium |
| cal_10 | 2024.12.09startup_a | 2958 | middle | True | cognitive_perturbation | CP_generative | smm_strategy | conf_high |
| cal_11 | 2024.12.23startup_a | 1491 | early | True | functional_reorientation | FR_elaboration | smm_strategy | conf_medium |
| cal_12 | 2024.12.23startup_b | 4971 | late | True | functional_reorientation | FR_elaboration | smm_task | conf_medium |
| cal_13 | 2025.03.17startup_b | 3428 | middle | False | functional_reorientation | FR_elaboration | smm_strategy | conf_medium |
| cal_14 | 2025.03.17startup_b | 4529 | late | False | cognitive_perturbation | CP_generative | smm_strategy | conf_medium |
| cal_15 | 2025.03.25startup_a | 305 | early | True | functional_reorientation | FR_attention | smm_goals | conf_medium |
| cal_16 | 2025.03.25startup_a | 3677 | late | False | cognitive_perturbation | CP_generative | smm_task | conf_medium |
| cal_17 | 2025.03.31startup_a | 1004 | early | False | cognitive_perturbation | CP_generative | smm_task | conf_high |
| cal_18 | 2025.03.31startup_b | 544 | early | False | functional_reorientation | FR_procedural | smm_strategy | conf_medium |
| cal_19 | 2025.04.07startup_b | 475 | early | False | cognitive_perturbation | CP_constraint | smm_goals | conf_high |
| cal_20 | 2025.04.14startup_a | 4155 | late | False | functional_reorientation | FR_elaboration | smm_task | conf_medium |

## Case-level summaries and justifications

| calibration_case_id | content_summary | justification |
|---|---|---|
| cal_01 | The team discusses two MVP paths: partnering with a supplier and finding an initial client to make the MVP concrete. | The team is elaborating an existing line of action (MVP development), detailing two concrete next steps without disrupting the shared frame. No competing interpretations or frame-challenging content appears; the conversation builds on the established problem and converts it into structured tasks. |
| cal_02 | Team members actively debate whether to prioritize Plugin or PARTNER_D as a strategic partner, contrasting risk and fit. | Competing strategic interpretations are explicitly contrasted: Speaker 3 and Speaker 2 favor Plugin for better fit and independence, while Speaker 1 questions whether partnering with Plugin would actually damage the PARTNER_D relationship. The divergence involves different assumptions about partner dynamics, making this a CP_divergence event. The SMM dimension affected is smm_strategy, as the team's shared plan for partner sequencing is under active dispute. |
| cal_03 | During a task-list review, a team member proposes explicitly quantifying the battery and hybrid vehicle market size as a strategic necessity. | Speaker 4 introduces a new conceptual need — to define and quantify the battery/hybrid market — beyond the ongoing task-list review, expanding the team's shared picture of what the project must deliver. This is CP_generative because the idea opens a new analytical space rather than opposing an existing assumption. Confidence is medium because the generative moment is embedded within procedural review, making the boundary somewhat diffuse. |
| cal_04 | The facilitator introduces a reframing strategy for accessing fire-department officials by positioning the startup as already operational rather than prospective. | The facilitator reveals a new strategic possibility: instead of presenting as a future project, the team should frame themselves as currently dealing with an EV charging issue at a real location, triggering a regulatory obligation to respond. This expands the team's conceptual space for accessing gatekeepers, making it CP_generative. The SMM dimension is smm_strategy because the team's plan for institutional access is fundamentally reoriented. |
| cal_05 | The facilitator and team develop a bottom-up method for estimating market size using average part prices from junkyards. | The discussion elaborates an existing analytical task (market sizing), detailing a practical methodology without disrupting the team's shared frame. The facilitator is helping refine how to approach an acknowledged task rather than introducing a new possibility or challenging an assumption. smm_task is affected because the team is clarifying the nature and scope of their market analysis deliverable. |
| cal_06 | The team discovers a well-connected Brazilian contact and a major electric-mobility investment fund, opening new partnership and investor paths. | The discovery of a new contact with ready-made industry connections and the identification of Evolution (an electric-mobility company with R$200M in regional investment) substantially expands the team's strategic horizon in ways that were not previously anticipated. This is CP_generative: new possibilities enter the conceptual space and alter the team's view of what partnerships and funding paths are available. The facilitator's reframing of how to use the contact before approaching the Indian partner reinforces the generative character of the event. |
| cal_07 | A team member clarifies that only used parts may be sourced, and identifies an unowned task for finding a client's requested part with pricing. | Speaker 3 establishes that the circular-economy commitment restricts part sourcing to used items, ruling out new-part platforms and narrowing the feasible search space. This is CP_constraint because a clarified limitation (used-only) changes what is permissible in the team's operation. The debate about used versus new sources (t=2715–2733) reflects the constraint being internalized. smm_constraints is the primary dimension affected. |
| cal_08 | The facilitator leads a structured 45-day goal review, confirming tracking status across operations, market, and finance. | The window is dominated by a structured check-in on progress metrics, reviewing whether each goal dimension is on track. This is FR_procedural: the team is moving through a standardized review protocol and coordinating next-step tasks without challenging the shared frame. The '99' mention adds a new thread but does not disrupt the overall logic. smm_strategy is affected because the team is aligning on plan status. |
| cal_09 | The team learns of a potentially better-positioned competitor with existing software embedded in multiple junkyards, limiting their assumed uniqueness. | The competitor's existing software network gives them catalogue access across junkyards, which introduces a new limitation on the team's assumed competitive position. This is CP_constraint because the rival's structural advantage constrains what the team can claim as unique and shapes what differentiation they must articulate. Confidence is medium because the competitor's status is still unconfirmed — they plan to meet him — and the window contains both threat framing and reframing as potential partner. |
| cal_10 | The facilitator introduces a four-stakeholder B2B sales framework — influencer, user, decision-maker, and final approver — expanding the team's view of how to sell. | The facilitator introduces a new conceptual model that reframes the team's sales challenge: instead of treating a gatekeeper as a blocker, they should sell to all four stakeholder types simultaneously. This is CP_generative because it opens a new strategic possibility and reorganizes the team's shared understanding of their sales process. smm_strategy is the affected dimension, as the team's approach to client acquisition is fundamentally enriched. |
| cal_11 | The team works out the MVP vehicle and charger logistics, discovering that one battery unit supports two simultaneous charging outputs. | The discussion elaborates the MVP execution plan, detailing which vehicles and charger configurations are feasible and setting targets for February–March. The revelation that one battery can support two charging outputs is a practical clarification that helps plan better rather than a frame-disrupting insight. FR_elaboration fits because the team is detailing an existing operational plan without challenging shared assumptions. |
| cal_12 | The team synthesizes customer discovery results, concluding that off-grid is the most promising segment based on two client responses out of four contacts. | The team is consolidating and interpreting their early customer discovery data, with the facilitator framing the 50% response rate as a reasonable funnel metric. This is FR_elaboration: the team is developing their understanding of an existing analytical task (segment validation) rather than introducing a frame-disrupting idea. smm_task is affected as the team refines their picture of what the market analysis should establish. |
| cal_13 | The facilitator rehearses the two-alternative persuasion framework for client pitches, reinforcing how to present the 'with us vs. without us' choice. | The facilitator is elaborating a pre-established sales framework (two-alternative pitch structure), reviewing its logic and connecting it to upcoming client conversations. This is FR_elaboration because the team is developing an existing strategic line rather than introducing a new one or challenging assumptions. smm_strategy is the affected dimension, as the team refines how they plan to execute partnership conversations. |
| cal_14 | The team learns that PARTNER_A will soon have used truck batteries available, opening a new supply-chain possibility worth pursuing. | The information that PARTNER_A's future truck operations will generate used batteries — a potential supply source not previously on the team's map — expands the conceptual space for input sourcing. This is CP_generative because it introduces a new possibility that alters the team's understanding of available partnerships. Confidence is medium because the timeline and quantity are uncertain and the discussion moves quickly to next-step actions. |
| cal_15 | A late-joining participant presents a one-page investor pitch and the team reviews market size figures for a Swedish-market investor. | The team redirects its attention to an investor pitch document being shown for the first time, reviewing market-size numbers and the appropriateness of the figures for a specific investor. This is FR_attention: the team focuses on a new informational artifact without the shared frame being disrupted. smm_goals is affected because the discussion centers on targets and criteria relevant to investor expectations. |
| cal_16 | The team realizes that pivoting to heavy vehicles makes their technology simpler and more reliable than the original light-vehicle target. | The facilitator and Speaker 5 jointly articulate a new insight: heavy-vehicle operations are more predictable and route-dedicated, which simplifies the scheduling and charging technology significantly compared to the light-vehicle approach. This is CP_generative because the realization expands the team's understanding of their own competitive advantage and changes what the product must be. smm_task is affected as the team revises its picture of the technical challenge. |
| cal_17 | A team member reports that a fleet operator spends R$7–8k per week on towing stranded EVs, validating a concrete and quantified market pain. | The discovery of a specific, quantified operational pain — thousands of reais per week in towing costs due to range anxiety — dramatically expands the team's understanding of their addressable problem. The operator had previously considered a battery bank solution but was blocked by cost, confirming both the pain and the barrier the team is positioned to solve. This is CP_generative because it opens new market possibilities and provides concrete evidence for a use case that was previously hypothetical. |
| cal_18 | The team coordinates three upcoming stakeholder meetings and reviews a progress score that increased from 4.5 to 5.5 on a cost metric. | The discussion centers on scheduling and logistics for three imminent meetings and tracking a score improvement. This is FR_procedural: the team is sequencing next steps and aligning on meeting arrangements without any frame-disrupting content. smm_strategy is affected as they are organizing the execution sequence for their business development activities. |
| cal_19 | A high-level evaluator tells the team their project is 2–3 years too early for the market, introducing a timing constraint on their roadmap. | Ronaldo's assessment that the venture would be easier to develop in two to three years is a credible external evaluation that forces the team to confront a timing constraint they had not fully acknowledged. This is CP_constraint because the limitation — market readiness — is now placed on the table by a qualified external source and must be factored into the team's priorities and goals. smm_goals is the primary dimension affected, as the intended timeline and commercialization targets are now in question. |
| cal_20 | The facilitator pushes the team to articulate that their mobile charging technology is equivalent to the best fixed fast-chargers for heavy vehicles. | The facilitator is helping the team sharpen their technical positioning claim — that their solution matches fixed fast chargers for trucks because large batteries require fast charging anyway. This is FR_elaboration because the team is detailing and clarifying an existing value-proposition line without challenging the shared strategic frame. smm_task is affected as the team refines its understanding of what their product actually delivers. |

## Human review queue (conf_low cases)

No conf_low cases in this calibration run. All 20 events were classifiable with medium or high confidence.

## Operational note

The pipeline stops here by design. The remaining 156 Entropy-UCL events should not be classified until this calibration report is reviewed and explicitly approved by the researcher. Once approved, run `classify_full_entropy_run.py` against all 176 events without overwriting these calibration files.
