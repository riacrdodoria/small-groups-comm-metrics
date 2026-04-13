# Step 05 Reclassification Report

**Date:** 2026-04-12  
**Model:** claude-sonnet-4-6 (temperature=0.0)  
**Events submitted for reclassification:** 155  
**Successfully reclassified:** 155  
**Errors:** 0  

## 1. Classification Changes

| Change type | n |
|---|---|
| trigger_type changed (CP↔FR) | 102 |
| trigger_type same, subtype changed | 34 |
| trigger_type and subtype unchanged | 19 |
| **Total reclassified** | **155** |

## 2. trigger_type Distribution: Before vs After

| trigger_type | before | after |
|---|---|---|
| cognitive_perturbation | 51 | 145 |
| functional_reorientation | 125 | 31 |

## 3. trigger_type Changes Detail

### CP → FR (4 events)

| event_id | orig_subtype | new_subtype |
|---|---|---|
| evt_020 | CP_generative | FR_social |
| evt_035 | CP_generative | FR_attention |
| evt_066 | CP_generative | FR_attention |
| evt_152 | CP_generative | FR_procedural |

### FR → CP (98 events)

| event_id | orig_subtype | new_subtype |
|---|---|---|
| evt_002 | FR_procedural | CP_generative |
| evt_008 | FR_elaboration | CP_generative |
| evt_010 | FR_elaboration | CP_generative |
| evt_013 | FR_elaboration | CP_invalidation |
| evt_014 | FR_elaboration | CP_invalidation |
| evt_015 | FR_elaboration | CP_generative |
| evt_016 | FR_elaboration | CP_divergence |
| evt_017 | FR_procedural | CP_invalidation |
| evt_018 | FR_procedural | CP_generative |
| evt_021 | FR_procedural | CP_generative |
| evt_023 | FR_procedural | CP_generative |
| evt_025 | FR_procedural | CP_generative |
| evt_026 | FR_procedural | CP_generative |
| evt_029 | FR_procedural | CP_constraint |
| evt_030 | FR_procedural | CP_divergence |
| evt_032 | FR_elaboration | CP_generative |
| evt_036 | FR_elaboration | CP_divergence |
| evt_038 | FR_elaboration | CP_divergence |
| evt_039 | FR_procedural | CP_invalidation |
| evt_040 | FR_elaboration | CP_divergence |
| evt_047 | FR_procedural | CP_constraint |
| evt_053 | FR_procedural | CP_divergence |
| evt_054 | FR_procedural | CP_invalidation |
| evt_055 | FR_elaboration | CP_generative |
| evt_056 | FR_procedural | CP_divergence |
| evt_058 | FR_elaboration | CP_invalidation |
| evt_060 | FR_elaboration | CP_generative |
| evt_061 | FR_procedural | CP_generative |
| evt_064 | FR_procedural | CP_constraint |
| evt_065 | FR_elaboration | CP_generative |
| evt_067 | FR_elaboration | CP_constraint |
| evt_068 | FR_elaboration | CP_constraint |
| evt_070 | FR_procedural | CP_invalidation |
| evt_071 | FR_elaboration | CP_generative |
| evt_073 | FR_procedural | CP_divergence |
| evt_075 | FR_elaboration | CP_constraint |
| evt_076 | FR_elaboration | CP_constraint |
| evt_077 | FR_elaboration | CP_generative |
| evt_080 | FR_procedural | CP_invalidation |
| evt_081 | FR_elaboration | CP_divergence |
| evt_084 | FR_procedural | CP_constraint |
| evt_085 | FR_procedural | CP_invalidation |
| evt_088 | FR_elaboration | CP_divergence |
| evt_089 | FR_elaboration | CP_generative |
| evt_090 | FR_procedural | CP_generative |
| evt_091 | FR_elaboration | CP_generative |
| evt_092 | FR_elaboration | CP_invalidation |
| evt_093 | FR_attention | CP_invalidation |
| evt_094 | FR_procedural | CP_invalidation |
| evt_096 | FR_procedural | CP_generative |
| evt_097 | FR_procedural | CP_invalidation |
| evt_098 | FR_elaboration | CP_generative |
| evt_101 | FR_attention | CP_generative |
| evt_102 | FR_elaboration | CP_constraint |
| evt_103 | FR_procedural | CP_generative |
| evt_105 | FR_attention | CP_divergence |
| evt_106 | FR_elaboration | CP_generative |
| evt_107 | FR_procedural | CP_constraint |
| evt_108 | FR_elaboration | CP_constraint |
| evt_109 | FR_elaboration | CP_generative |
| evt_110 | FR_elaboration | CP_generative |
| evt_111 | FR_procedural | CP_generative |
| evt_112 | FR_elaboration | CP_generative |
| evt_113 | FR_elaboration | CP_generative |
| evt_114 | FR_elaboration | CP_invalidation |
| evt_117 | FR_elaboration | CP_invalidation |
| evt_118 | FR_elaboration | CP_generative |
| evt_119 | FR_procedural | CP_divergence |
| evt_120 | FR_elaboration | CP_generative |
| evt_122 | FR_procedural | CP_constraint |
| evt_123 | FR_elaboration | CP_constraint |
| evt_124 | FR_procedural | CP_divergence |
| evt_125 | FR_procedural | CP_generative |
| evt_128 | FR_elaboration | CP_divergence |
| evt_130 | FR_procedural | CP_constraint |
| evt_132 | FR_elaboration | CP_divergence |
| evt_136 | FR_elaboration | CP_invalidation |
| evt_139 | FR_elaboration | CP_generative |
| evt_140 | FR_elaboration | CP_divergence |
| evt_143 | FR_elaboration | CP_divergence |
| evt_144 | FR_elaboration | CP_divergence |
| evt_146 | FR_elaboration | CP_divergence |
| evt_148 | FR_elaboration | CP_invalidation |
| evt_149 | FR_elaboration | CP_generative |
| evt_151 | FR_elaboration | CP_generative |
| evt_154 | FR_elaboration | CP_generative |
| evt_157 | FR_elaboration | CP_generative |
| evt_158 | FR_elaboration | CP_constraint |
| evt_159 | FR_attention | CP_constraint |
| evt_163 | FR_elaboration | CP_generative |
| evt_164 | FR_procedural | CP_divergence |
| evt_165 | FR_procedural | CP_divergence |
| evt_166 | FR_procedural | CP_constraint |
| evt_171 | FR_elaboration | CP_generative |
| evt_172 | FR_elaboration | CP_generative |
| evt_173 | FR_elaboration | CP_generative |
| evt_174 | FR_elaboration | CP_generative |
| evt_176 | FR_elaboration | CP_divergence |

## 4. All Reclassified Events

| event_id | orig_type | orig_subtype | new_type | new_subtype | changed |
|---|---|---|---|---|---|
| evt_001 | FR | FR_role | FR | FR_attention | ✓ |
| evt_002 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_004 | CP | CP_constraint | CP | CP_invalidation | ✓ |
| evt_005 | FR | FR_procedural | FR | FR_attention | ✓ |
| evt_006 | FR | FR_elaboration | FR | FR_procedural | ✓ |
| evt_007 | CP | CP_constraint | CP | CP_constraint | — |
| evt_008 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_010 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_011 | CP | CP_generative | CP | CP_divergence | ✓ |
| evt_013 | FR | FR_elaboration | CP | CP_invalidation | ✓ |
| evt_014 | FR | FR_elaboration | CP | CP_invalidation | ✓ |
| evt_015 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_016 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_017 | FR | FR_procedural | CP | CP_invalidation | ✓ |
| evt_018 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_020 | CP | CP_generative | FR | FR_social | ✓ |
| evt_021 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_022 | CP | CP_generative | CP | CP_generative | — |
| evt_023 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_025 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_026 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_027 | CP | CP_generative | CP | CP_generative | — |
| evt_028 | FR | FR_procedural | FR | FR_social | ✓ |
| evt_029 | FR | FR_procedural | CP | CP_constraint | ✓ |
| evt_030 | FR | FR_procedural | CP | CP_divergence | ✓ |
| evt_032 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_034 | CP | CP_generative | CP | CP_constraint | ✓ |
| evt_035 | CP | CP_generative | FR | FR_attention | ✓ |
| evt_036 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_037 | CP | CP_generative | CP | CP_generative | — |
| evt_038 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_039 | FR | FR_procedural | CP | CP_invalidation | ✓ |
| evt_040 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_041 | CP | CP_constraint | CP | CP_invalidation | ✓ |
| evt_043 | CP | CP_generative | CP | CP_invalidation | ✓ |
| evt_044 | FR | FR_attention | FR | FR_elaboration | ✓ |
| evt_045 | FR | FR_elaboration | FR | FR_procedural | ✓ |
| evt_047 | FR | FR_procedural | CP | CP_constraint | ✓ |
| evt_048 | CP | CP_generative | CP | CP_generative | — |
| evt_049 | CP | CP_constraint | CP | CP_constraint | — |
| evt_050 | CP | CP_generative | CP | CP_generative | — |
| evt_051 | CP | CP_invalidation | CP | CP_divergence | ✓ |
| evt_053 | FR | FR_procedural | CP | CP_divergence | ✓ |
| evt_054 | FR | FR_procedural | CP | CP_invalidation | ✓ |
| evt_055 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_056 | FR | FR_procedural | CP | CP_divergence | ✓ |
| evt_057 | FR | FR_elaboration | FR | FR_procedural | ✓ |
| evt_058 | FR | FR_elaboration | CP | CP_invalidation | ✓ |
| evt_059 | CP | CP_constraint | CP | CP_invalidation | ✓ |
| evt_060 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_061 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_063 | CP | CP_generative | CP | CP_generative | — |
| evt_064 | FR | FR_procedural | CP | CP_constraint | ✓ |
| evt_065 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_066 | CP | CP_generative | FR | FR_attention | ✓ |
| evt_067 | FR | FR_elaboration | CP | CP_constraint | ✓ |
| evt_068 | FR | FR_elaboration | CP | CP_constraint | ✓ |
| evt_069 | CP | CP_generative | CP | CP_invalidation | ✓ |
| evt_070 | FR | FR_procedural | CP | CP_invalidation | ✓ |
| evt_071 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_073 | FR | FR_procedural | CP | CP_divergence | ✓ |
| evt_074 | FR | FR_elaboration | FR | FR_procedural | ✓ |
| evt_075 | FR | FR_elaboration | CP | CP_constraint | ✓ |
| evt_076 | FR | FR_elaboration | CP | CP_constraint | ✓ |
| evt_077 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_078 | CP | CP_generative | CP | CP_constraint | ✓ |
| evt_079 | FR | FR_elaboration | FR | FR_procedural | ✓ |
| evt_080 | FR | FR_procedural | CP | CP_invalidation | ✓ |
| evt_081 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_083 | FR | FR_attention | FR | FR_procedural | ✓ |
| evt_084 | FR | FR_procedural | CP | CP_constraint | ✓ |
| evt_085 | FR | FR_procedural | CP | CP_invalidation | ✓ |
| evt_086 | CP | CP_constraint | CP | CP_constraint | — |
| evt_087 | CP | CP_generative | CP | CP_constraint | ✓ |
| evt_088 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_089 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_090 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_091 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_092 | FR | FR_elaboration | CP | CP_invalidation | ✓ |
| evt_093 | FR | FR_attention | CP | CP_invalidation | ✓ |
| evt_094 | FR | FR_procedural | CP | CP_invalidation | ✓ |
| evt_095 | CP | CP_constraint | CP | CP_generative | ✓ |
| evt_096 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_097 | FR | FR_procedural | CP | CP_invalidation | ✓ |
| evt_098 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_099 | CP | CP_generative | CP | CP_divergence | ✓ |
| evt_100 | FR | FR_elaboration | FR | FR_elaboration | — |
| evt_101 | FR | FR_attention | CP | CP_generative | ✓ |
| evt_102 | FR | FR_elaboration | CP | CP_constraint | ✓ |
| evt_103 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_104 | CP | CP_generative | CP | CP_constraint | ✓ |
| evt_105 | FR | FR_attention | CP | CP_divergence | ✓ |
| evt_106 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_107 | FR | FR_procedural | CP | CP_constraint | ✓ |
| evt_108 | FR | FR_elaboration | CP | CP_constraint | ✓ |
| evt_109 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_110 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_111 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_112 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_113 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_114 | FR | FR_elaboration | CP | CP_invalidation | ✓ |
| evt_115 | CP | CP_generative | CP | CP_invalidation | ✓ |
| evt_116 | CP | CP_generative | CP | CP_constraint | ✓ |
| evt_117 | FR | FR_elaboration | CP | CP_invalidation | ✓ |
| evt_118 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_119 | FR | FR_procedural | CP | CP_divergence | ✓ |
| evt_120 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_121 | CP | CP_generative | CP | CP_divergence | ✓ |
| evt_122 | FR | FR_procedural | CP | CP_constraint | ✓ |
| evt_123 | FR | FR_elaboration | CP | CP_constraint | ✓ |
| evt_124 | FR | FR_procedural | CP | CP_divergence | ✓ |
| evt_125 | FR | FR_procedural | CP | CP_generative | ✓ |
| evt_127 | FR | FR_elaboration | FR | FR_procedural | ✓ |
| evt_128 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_130 | FR | FR_procedural | CP | CP_constraint | ✓ |
| evt_131 | CP | CP_generative | CP | CP_generative | — |
| evt_132 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_133 | CP | CP_constraint | CP | CP_constraint | — |
| evt_134 | FR | FR_elaboration | FR | FR_procedural | ✓ |
| evt_136 | FR | FR_elaboration | CP | CP_invalidation | ✓ |
| evt_137 | CP | CP_generative | CP | CP_generative | — |
| evt_138 | FR | FR_elaboration | FR | FR_social | ✓ |
| evt_139 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_140 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_143 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_144 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_145 | FR | FR_procedural | FR | FR_attention | ✓ |
| evt_146 | FR | FR_elaboration | CP | CP_divergence | ✓ |
| evt_148 | FR | FR_elaboration | CP | CP_invalidation | ✓ |
| evt_149 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_150 | CP | CP_generative | CP | CP_generative | — |
| evt_151 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_152 | CP | CP_generative | FR | FR_procedural | ✓ |
| evt_153 | CP | CP_generative | CP | CP_invalidation | ✓ |
| evt_154 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_155 | FR | FR_procedural | FR | FR_procedural | — |
| evt_156 | CP | CP_generative | CP | CP_constraint | ✓ |
| evt_157 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_158 | FR | FR_elaboration | CP | CP_constraint | ✓ |
| evt_159 | FR | FR_attention | CP | CP_constraint | ✓ |
| evt_161 | CP | CP_generative | CP | CP_generative | — |
| evt_162 | CP | CP_generative | CP | CP_generative | — |
| evt_163 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_164 | FR | FR_procedural | CP | CP_divergence | ✓ |
| evt_165 | FR | FR_procedural | CP | CP_divergence | ✓ |
| evt_166 | FR | FR_procedural | CP | CP_constraint | ✓ |
| evt_167 | FR | FR_procedural | FR | FR_procedural | — |
| evt_168 | CP | CP_generative | CP | CP_divergence | ✓ |
| evt_169 | CP | CP_generative | CP | CP_invalidation | ✓ |
| evt_171 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_172 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_173 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_174 | FR | FR_elaboration | CP | CP_generative | ✓ |
| evt_175 | FR | FR_social | FR | FR_social | — |
| evt_176 | FR | FR_elaboration | CP | CP_divergence | ✓ |

