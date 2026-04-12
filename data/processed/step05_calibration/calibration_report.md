# Step 05 calibration classification report

This report documents the approved 20-case calibration run for Step 05. Each case was classified from a transcript window centered on the Entropy-UCL peak (`peak_second ± 180 s`), with the transcript kept in its source language and all output labels and justifications standardized in English. The purpose of this stage is to inspect the CP versus FR coding behavior before launching the remaining 156 classifications.

## Calibration sample coverage

| Requirement | Target | Achieved |
|---|---:|---:|
| Sample size | 20 | 20 |
| Distinct meetings | 5 | 18 |
| Include meetings | 5 | 12 |
| Include-with-caution meetings | 2 | 6 |
| Joint corroborated = True | 8 | 10 |
| Joint corroborated = False | 8 | 10 |
| Middle or late events | 6 | 12 |
| Max cases from one meeting | 2 | 2 |

## Trigger-type distribution

| trigger_type | n | % |
|---|---:|---:|
| functional_reorientation | 20 | 100.0% |

Across the approved calibration set, `cognitive_perturbation` accounts for 0 cases (0.0%), whereas `functional_reorientation` accounts for 20 cases (100.0%). This split provides an initial check on whether the Step 05 prompt is yielding a plausible separation between frame-disrupting episodes and coordination-oriented reorientation episodes.

## Trigger-subtype distribution

| trigger_subtype | n | % |
|---|---:|---:|
| FR_attention | 20 | 100.0% |

## SMM-dimension distribution

| smm_dimension | n | % |
|---|---:|---:|
| smm_none | 20 | 100.0% |

## Confidence distribution

| confidence | n | % |
|---|---:|---:|
| conf_low | 20 | 100.0% |

## Trigger type by joint corroboration

| joint_corroborated | cognitive_perturbation | functional_reorientation | total |
|---|---:|---:|---:|
| False | 0 | 10 | 10 |
| True | 0 | 10 | 10 |

## Trigger type by meeting quality

| quality_label | cognitive_perturbation | functional_reorientation | total |
|---|---:|---:|---:|
| include | 0 | 12 | 12 |
| include_with_caution | 0 | 8 | 8 |

## Case-level classifications

| calibration_case_id | meeting_id | peak_second | timing_bin | joint_corroborated | trigger_type | trigger_subtype | smm_dimension | confidence |
|---|---|---:|---|---|---|---|---|---|
| cal_01 | 2024.10.14startup_a | 2169 | middle | False | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_02 | 2024.10.25startup_a | 4115 | late | False | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_03 | 2024.10.28startup_b | 2143 | middle | True | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_04 | 2024.11.04startup_a | 2067 | middle | True | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_05 | 2024.11.04startup_b | 2954 | middle | True | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_06 | 2024.11.11startup_a | 650 | early | False | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_07 | 2024.11.11startup_b | 2732 | middle | True | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_08 | 2024.11.18startup_a | 714 | early | True | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_09 | 2024.11.18startup_b | 321 | early | True | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_10 | 2024.12.09startup_a | 2958 | middle | True | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_11 | 2024.12.23startup_a | 1491 | early | True | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_12 | 2024.12.23startup_b | 4971 | late | True | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_13 | 2025.03.17startup_b | 3428 | middle | False | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_14 | 2025.03.17startup_b | 4529 | late | False | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_15 | 2025.03.25startup_a | 305 | early | True | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_16 | 2025.03.25startup_a | 3677 | late | False | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_17 | 2025.03.31startup_a | 1004 | early | False | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_18 | 2025.03.31startup_b | 544 | early | False | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_19 | 2025.04.07startup_b | 475 | early | False | functional_reorientation | FR_attention | smm_none | conf_low |
| cal_20 | 2025.04.14startup_a | 4155 | late | False | functional_reorientation | FR_attention | smm_none | conf_low |

## Case-level summaries and justifications

| calibration_case_id | content_summary | justification |
|---|---|---|
| cal_01 | The segment centers on: transformar isso agora. | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_02 | The segment centers on: E eu acho que tem muito mais Fit com que a gente quer entregar solução. A plugin eu acho que a gente for pensar na ge... | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_03 | The segment centers on: De 31 a 34 foi o que a gente | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_04 | The segment centers on: Eu acho que a gente tinha que | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_05 | The segment centers on: É isso mesmo. | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_06 | The segment centers on: Por isso é espetacular, viu? Não tava no radar surgiu de repente aí essa contato. | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_07 | The segment centers on: Pode ser que alguém diga não nem de graça, eu quero entrar. Me ligue de quando tiver então fase, né? Porque tudo. | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_08 | The segment centers on: Sim, acho que pode seguir tá tudo | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_09 | The segment centers on: É a gente tem alguns detalhes para te passar e ver sua opinião, porque [UNRESOLVED_ENTITY] a gente não conseguiu cheg... | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_10 | The segment centers on: Boa eu vou eu vou então, vou fazer o | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_11 | The segment centers on: é a gente acredita que | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_12 | The segment centers on: Terminar isso com nota 8 do que tentar um 10 e não consegui terminar. | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_13 | The segment centers on: Então vamos lá. | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_14 | The segment centers on: Da [PARTNER_A] aqui eles vão fazer um coisa com [UNRESOLVED_ENTITY] [PARTNER_D], né? Que a gente tinha comentado. | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_15 | The segment centers on: Bom dia, [PERSON_E]. | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_16 | The segment centers on: [UNRESOLVED_ENTITY] a gente estava em quatro A gente estava em quatro na tecnologia com o objetivo de chegar em 5. Se... | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_17 | The segment centers on: Então esse é um esse é o entrevista que tava faltando. | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_18 | The segment centers on: Tá certo | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_19 | The segment centers on: sim | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |
| cal_20 | The segment centers on: A mesma coisa são um [UNRESOLVED_ENTITY] rápido. | Model parsing failed during the calibration run: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-2kgpv*************hnXf. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401} |

## Operational note

The pipeline stops here by design. The remaining 156 Entropy-UCL events should not be classified until this calibration report is reviewed and explicitly approved.
