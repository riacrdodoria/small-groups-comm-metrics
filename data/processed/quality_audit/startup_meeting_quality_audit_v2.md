# Startup Meeting Quality Audit v2

This audit evaluates the 34 retained startup meetings for paper readiness using structural validation, transcript-level diagnostics, and distribution-based anomaly screening. The goal is to identify whether any retained meeting still shows evidence of corruption or requires caution.

## Overall recommendation

The audit classified **26 meetings as `include`**, **8 as `include_with_caution`**, and **0 as `exclude`**.

A meeting was marked `exclude` only if it showed structural failure, implausibly low content, or internal inconsistencies. A meeting was marked `include_with_caution` if it passed structural checks but showed unusually high rates of placeholders, flagged entities, long internal gaps, or other outlier patterns.

## Audit table

| meeting_id          | final_label          |   duration_seconds |   n_turns |   n_speakers |   top_speaker_pct |   placeholder_turn_rate |   review_flagged_rate |   max_gap_seconds | caution_flags                                | severe_flags   |
|:--------------------|:---------------------|-------------------:|----------:|-------------:|------------------:|------------------------:|----------------------:|------------------:|:---------------------------------------------|:---------------|
| 2024.10.14startup_a | include              |               5485 |       504 |            4 |             59.3  |                   0.173 |                 0.167 |                87 |                                              |                |
| 2024.10.25startup_a | include              |               5257 |       513 |            4 |             42.77 |                   0.251 |                 0.23  |                74 |                                              |                |
| 2024.10.28startup_b | include              |               5421 |       532 |            4 |             39.12 |                   0.175 |                 0.19  |                55 |                                              |                |
| 2024.11.04startup_a | include              |               5257 |       420 |            4 |             46.69 |                   0.29  |                 0.217 |                76 |                                              |                |
| 2024.11.04startup_b | include              |               5069 |       461 |            4 |             43.35 |                   0.163 |                 0.161 |                77 |                                              |                |
| 2024.11.11startup_a | include              |               5259 |       431 |            4 |             40.97 |                   0.225 |                 0.193 |                73 |                                              |                |
| 2024.11.11startup_b | include              |               5557 |       670 |            4 |             35.43 |                   0.155 |                 0.167 |                68 |                                              |                |
| 2024.11.18startup_a | include              |               5378 |       368 |            4 |             43.73 |                   0.228 |                 0.193 |                93 |                                              |                |
| 2024.11.18startup_b | include              |               5338 |       507 |            4 |             33.47 |                   0.181 |                 0.189 |                74 |                                              |                |
| 2024.12.09startup_a | include              |               5389 |       514 |            4 |             46.14 |                   0.253 |                 0.198 |                76 |                                              |                |
| 2024.12.13startup_a | include              |               5205 |       491 |            3 |             43.41 |                   0.222 |                 0.175 |                83 |                                              |                |
| 2024.12.16startup_b | include              |               5283 |       662 |            4 |             32.59 |                   0.137 |                 0.119 |                66 |                                              |                |
| 2024.12.23startup_a | include              |               5340 |       439 |            4 |             34.24 |                   0.237 |                 0.226 |                91 |                                              |                |
| 2024.12.23startup_b | include              |               5511 |       531 |            4 |             41.98 |                   0.186 |                 0.171 |                70 |                                              |                |
| 2025.01.06startup_a | include              |               5684 |       657 |            3 |             40.88 |                   0.183 |                 0.196 |                77 |                                              |                |
| 2025.01.06startup_b | include              |               5846 |       501 |            3 |             44.86 |                   0.198 |                 0.214 |               195 |                                              |                |
| 2025.01.13startup_a | include              |               5418 |       415 |            4 |             46.82 |                   0.236 |                 0.212 |                87 |                                              |                |
| 2025.01.13startup_b | include              |               5654 |       471 |            4 |             50.77 |                   0.195 |                 0.187 |                77 |                                              |                |
| 2025.02.10startup_b | include              |               5413 |       481 |            3 |             47.67 |                   0.185 |                 0.22  |                92 |                                              |                |
| 2025.02.24startup_a | include              |               5132 |       391 |            4 |             52.06 |                   0.235 |                 0.246 |                83 |                                              |                |
| 2025.02.24startup_b | include              |               5124 |       405 |            4 |             57.37 |                   0.222 |                 0.2   |                70 |                                              |                |
| 2025.03.02startup_a | include              |               5258 |       324 |            4 |             38.45 |                   0.284 |                 0.253 |                82 |                                              |                |
| 2025.03.17startup_a | include              |               5271 |       386 |            5 |             50.74 |                   0.29  |                 0.269 |               103 |                                              |                |
| 2025.03.24startup_b | include              |               5274 |       559 |            5 |             46.71 |                   0.154 |                 0.148 |                81 |                                              |                |
| 2025.04.07startup_a | include              |               5932 |       542 |            4 |             42.42 |                   0.22  |                 0.183 |                68 |                                              |                |
| 2025.04.14startup_b | include              |               5207 |       417 |            5 |             55.57 |                   0.225 |                 0.204 |                76 |                                              |                |
| 2024.10.14startup_b | include_with_caution |               6044 |       858 |            4 |             49.79 |                   0.097 |                 0.073 |               376 | outlier_turn_count; large_within_meeting_gap |                |
| 2024.12.02startup_b | include_with_caution |               5420 |       922 |            4 |             31.99 |                   0.082 |                 0.079 |                77 | outlier_turn_count                           |                |
| 2025.03.17startup_b | include_with_caution |               6353 |       718 |            5 |             53.38 |                   0.189 |                 0.189 |                69 | outlier_duration                             |                |
| 2025.03.25startup_a | include_with_caution |               5114 |       358 |            5 |             50.5  |                   0.318 |                 0.257 |               158 | high_placeholder_rate                        |                |
| 2025.03.31startup_a | include_with_caution |               5127 |       357 |            5 |             43.64 |                   0.277 |                 0.213 |               309 | large_within_meeting_gap                     |                |
| 2025.03.31startup_b | include_with_caution |               6325 |       441 |            5 |             55.82 |                   0.261 |                 0.247 |               100 | outlier_duration                             |                |
| 2025.04.07startup_b | include_with_caution |               6482 |       767 |            5 |             43.17 |                   0.181 |                 0.138 |                65 | outlier_duration; outlier_turn_count         |                |
| 2025.04.14startup_a | include_with_caution |               6224 |       475 |            4 |             55.97 |                   0.286 |                 0.267 |               278 | outlier_duration                             |                |

## Criteria used

| Criterion family | Rule | Consequence |
| --- | --- | --- |
| Structural validation | Any failed validation field in `lsh_validation.csv` | Exclude |
| Internal consistency | Transcript turn count or duration does not match processed outputs | Exclude |
| Minimal plausibility | Duration < 30 minutes, turns < 150, speakers < 3, or empty text rate > 2% | Exclude |
| Outlier screening | Tukey-fence outlier on duration, turns, one-word rate, placeholder rate, review-flag rate, max gap, or speaker dominance | Include with caution |
| Transcript cleanliness | Placeholder, unresolved-entity, or review-flag rates above Tukey fences or high fixed thresholds; or median tokens per turn < 2 | Include with caution |

## Distribution thresholds

| Metric | Lower fence | Upper fence |
| --- | ---: | ---: |
| duration_seconds | 4698.500 | 6188.500 |
| n_turns | 235.125 | 722.125 |
| one_word_turn_rate | 0.019 | 0.136 |
| placeholder_turn_rate | 0.081 | 0.348 |
| review_flagged_rate | 0.102 | 0.290 |
| unresolved_entity_turn_rate | 0.086 | 0.216 |
| max_gap_seconds | 45.500 | 119.500 |
| top_speaker_pct | 27.037 | 64.865 |

## Meetings marked include_with_caution

- **2024.10.14startup_b**: Caution flags: outlier_turn_count, large_within_meeting_gap
- **2024.12.02startup_b**: Caution flags: outlier_turn_count
- **2025.03.17startup_b**: Caution flags: outlier_duration
- **2025.03.25startup_a**: Caution flags: high_placeholder_rate
- **2025.03.31startup_a**: Caution flags: large_within_meeting_gap
- **2025.03.31startup_b**: Caution flags: outlier_duration
- **2025.04.07startup_b**: Caution flags: outlier_duration, outlier_turn_count
- **2025.04.14startup_a**: Caution flags: outlier_duration

