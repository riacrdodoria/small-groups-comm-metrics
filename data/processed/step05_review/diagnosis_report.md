# Step 05 — Diagnóstico de Viés: Prompt Corrigido

**Data:** 2026-04-13  
**Casos analisados:** 40 (20 gold_standard + 20 fr_to_cp_flip)  
**Erros API:** 0

---

## 1. Distribuição das classificações

| Version | cognitive_perturbation | functional_reorientation |
|---------|----------------------|--------------------------|
| v1 (original in-context) | 11 | 29 |
| v2 (API reclassify — prompt antigo) | 31 | 9 |
| corrected (API — prompt corrigido) | 7 | 33 |

---

## 2. Taxas de concordância (trigger_type)

| Comparação | N concordante | Total | % |
|-----------|--------------|-------|---|
| corrected = v1 | 30 | 40 | 75.0% |
| corrected = v2 | 16 | 40 | 40.0% |
| corrected = gold_standard (20 casos) | 13 | 20 | 65.0% |

### Padrões de concordância (todos os 40 casos)

| Padrão | N |
|--------|---|
| corrected = v1 = v2 (todos concordam) | 13 |
| corrected = v1 ≠ v2 (prompt corrigido concorda com original) | 17 |
| corrected = v2 ≠ v1 (prompt corrigido concorda com reclassificado) | 3 |
| corrected ≠ v1 E corrected ≠ v2 (terceira classificação) | 7 |

### Por grupo

| Grupo | corrected=v1 | corrected=v2 | corrected=gold | N |
|-------|-------------|-------------|----------------|---|
| gold_standard | 13/20 (65%) | 13/20 (65%) | 13/20 (65%) | 20 |
| fr_to_cp_flip | 17/20 (85%) | 3/20 (15%) | — | 20 |

---

## 3. Cinco casos com maior divergência entre versões

### evt_019 (gold_standard) — peak  conf_medium

| Version | trigger_type | subtype |
|---------|-------------|---------|
| v1 | cognitive_perturbation | CP_generative |
| v2 | cognitive_perturbation | CP_generative |
| corrected | functional_reorientation | FR_procedural |

**v1 summary:** During a task-list review, a team member proposes explicitly quantifying the battery and hybrid vehicle market size as a...

**v2 summary:** During a task-list review, a team member proposes explicitly quantifying the battery and hybrid vehicle market size as a...

**corrected summary:** Team reviews and closes backlog items (36, 37, 38), assigns market research on batteries/EVs to Speaker 4, then surfaces...

**corrected justification:** The excerpt shows routine backlog triage and task assignment (items 36–38, ownership of market sizing) — classic FR. The supply-chain concern raised by Speaker 3 (t=2264) introduces a potential constraint, but the team immediately defers resolution to upcoming scheduled visits rather than revising t...

---

### evt_024 (gold_standard) — peak  conf_medium

| Version | trigger_type | subtype |
|---------|-------------|---------|
| v1 | cognitive_perturbation | CP_generative |
| v2 | cognitive_perturbation | CP_generative |
| corrected | functional_reorientation | FR_elaboration |

**v1 summary:** The facilitator introduces a reframing strategy for accessing fire-department officials by positioning the startup as al...

**v2 summary:** The facilitator introduces a reframing strategy for accessing fire-department officials by positioning the startup as al...

**corrected summary:** Speaker 1 reframes a stalled regulatory contact strategy, then Speaker 3 proposes discarding two risk items (policy ince...

**corrected justification:** Two distinct moves occur: Speaker 1 introduces a tactical reframing for approaching fire department contacts (present an MVP scenario rather than a future project), which enriches but does not disrupt the existing plan. Speaker 3 then proposes discarding risk items as uncontrollable externals, which...

---

### evt_042 (gold_standard) — peak  conf_medium

| Version | trigger_type | subtype |
|---------|-------------|---------|
| v1 | cognitive_perturbation | CP_constraint |
| v2 | cognitive_perturbation | CP_constraint |
| corrected | functional_reorientation | FR_role |

**v1 summary:** A team member clarifies that only used parts may be sourced, and identifies an unowned task for finding a client's reque...

**v2 summary:** A team member clarifies that only used parts may be sourced, and identifies an unowned task for finding a client's reque...

**corrected summary:** Team discovers an unresolved customer request (part search for Veyron) with no assigned owner, then debates splitting th...

**corrected justification:** Speaker 3 flags that nobody owns the part-search task and a client is waiting for a response — this reveals an incomplete assumption about task coverage. However, the team immediately moves into assigning owners, splitting the task into desmanche vs. online searches, and scheduling a reply. The entr...

---

### evt_062 (gold_standard) — peak  conf_high

| Version | trigger_type | subtype |
|---------|-------------|---------|
| v1 | cognitive_perturbation | CP_generative |
| v2 | cognitive_perturbation | CP_generative |
| corrected | functional_reorientation | FR_procedural |

**v1 summary:** The facilitator introduces a four-stakeholder B2B sales framework — influencer, user, decision-maker, and final approver...

**v2 summary:** The facilitator introduces a four-stakeholder B2B sales framework — influencer, user, decision-maker, and final approver...

**corrected summary:** Team transitions from handling a stakeholder contact issue to collectively building an interview script with open questi...

**corrected justification:** The excerpt shows a topic switch from managing a 'decisor vs. influencer' stakeholder situation to preparing discovery questions for a partner meeting. Speaker 2 introduces the idea of a structured 'roteirinho' of open questions, and the team immediately begins generating them collaboratively. This ...

---

### evt_129 (gold_standard) — peak  conf_medium

| Version | trigger_type | subtype |
|---------|-------------|---------|
| v1 | cognitive_perturbation | CP_generative |
| v2 | cognitive_perturbation | CP_generative |
| corrected | functional_reorientation | FR_procedural |

**v1 summary:** The team learns that PARTNER_A will soon have used truck batteries available, opening a new supply-chain possibility wor...

**v2 summary:** The team learns that PARTNER_A will soon have used truck batteries available, opening a new supply-chain possibility wor...

**corrected summary:** Team navigates a chain of partner contacts for PARTNER_A/PARTNER_D outreach, then shifts to assigning letter-of-intent d...

**corrected justification:** The excerpt shows sequential topic shifts — contact chain mapping, document ownership dispute (Speakers 4/5 disagree on who remembers the letter-of-intent context), and mentor reframing client vs. partner priorities — but none constitute frame disruption. The memory gap about the document is acknowl...

---

## 4. Cinco casos onde corrected = v1 ≠ v2 (prompt corrigido reverte para original)

### evt_173 (fr_to_cp_flip)

| Version | trigger_type | subtype |
|---------|-------------|---------|
| v1 | functional_reorientation | FR_elaboration |
| v2 | cognitive_perturbation | CP_generative |
| corrected | functional_reorientation | FR_elaboration |

**v2 summary:** Speaker 1 reframes the startup's core competitive identity by reminding the team that their original differentiator was ...

**corrected summary:** Mentor reframes startup's positioning by highlighting mobile charging as the core differentiator, explaining how three p...

**corrected justification:** The discussion elaborates an existing pitch deck structure — slide design, partner positioning, customer segmentation — without revealing contradictions or forcing plan revision. Speaker 1 reinforces the mobile differentiator as already established ('vocês começaram com isso'), and the team collecti...

---

### evt_025 (fr_to_cp_flip)

| Version | trigger_type | subtype |
|---------|-------------|---------|
| v1 | functional_reorientation | FR_procedural |
| v2 | cognitive_perturbation | CP_generative |
| corrected | functional_reorientation | FR_procedural |

**v2 summary:** Speaker 1 introduces a strategic planning framework distinguishing between uncontrollable external variables (interest r...

**corrected summary:** Team systematically discards multiple external variables (EV incentives, EV sales growth, energy prices) from their risk...

**corrected justification:** The excerpt shows coordinated pruning of a risk/scenario list using an agreed framework introduced by Speaker 1 (internal vs. external control variables). No divergence, invalidation, or forced revision occurs — members rapidly converge and extend the same logic across items 23, 17, 18. The entropy ...

---

### evt_090 (fr_to_cp_flip)

| Version | trigger_type | subtype |
|---------|-------------|---------|
| v1 | functional_reorientation | FR_procedural |
| v2 | cognitive_perturbation | CP_generative |
| corrected | functional_reorientation | FR_elaboration |

**v2 summary:** Speaker 1 introduces the concept of 'toneladas equivalentes de petróleo' (tonnes of oil equivalent) as a standardized en...

**corrected summary:** Speaker 1 introduces 'toneladas equivalentes de petróleo' as a standard energy equivalence unit from electricity market ...

**corrected justification:** Speaker 1 introduces a domain-specific methodology (TEP units from energy forecasting) that enriches the team's existing fuel equivalence approach. Speaker 3 confirms they already attempted something similar via BTU/barrel conversions. This is additive elaboration — the new concept aligns with and r...

---

### evt_077 (fr_to_cp_flip)

| Version | trigger_type | subtype |
|---------|-------------|---------|
| v1 | functional_reorientation | FR_elaboration |
| v2 | cognitive_perturbation | CP_generative |
| corrected | functional_reorientation | FR_elaboration |

**v2 summary:** Around t=4155–4346s, the conversation shifts from technical charger specifications to a cascade of field-interview insig...

**corrected summary:** Team integrates field interview findings—customer comfort, security, and hidden costs of public charging—into pricing an...

**corrected justification:** The discussion synthesizes customer interview data (comfort, security, hidden costs like VIP parking and café spending) to reinforce rather than disrupt the existing value proposition. Speaker 2 explicitly notes 'vocês tinham colocado na no Pit' confirming continuity with prior framing. New informat...

---

### evt_071 (fr_to_cp_flip)

| Version | trigger_type | subtype |
|---------|-------------|---------|
| v1 | functional_reorientation | FR_elaboration |
| v2 | cognitive_perturbation | CP_generative |
| corrected | functional_reorientation | FR_elaboration |

**v2 summary:** At the peak second (t=4513), Speaker 3 proposes sending an email to a prior contact to clarify a tax benefit question ra...

**corrected summary:** Team debates MVP validation strategy, target customer size, and business model boundaries; mentor (Speaker 1) reframes b...

**corrected justification:** Speaker 1 introduces a reframing of the battery's value proposition around reliability and maintenance responsibility, and explicitly questions whether investigating that market segment is worth the cost. Speaker 3 clarifies the business model boundary (product vs. service guarantee). These contribu...

---

## 5. Interpretação

*(A preencher após revisão dos resultados.)*
