# Frozen Result Schema

The method-specific stored schemas differ, but the common result contract includes the following audited fields where applicable:

| Field | Meaning | D0 | D1 | D2 V1/V2 |
|---|---|---|---|---|
| method / policy identity | scientific method authority | checked | checked | checked |
| prediction identity/hash | exact label-blind input | checked, durable | object/hash evidence, weaker pre-label gate | checked, durable |
| label authority/hash | exact test1 label contract | checked | checked | checked |
| row count/order | 54,000 aligned physical rows | checked | opportunity-to-row closure checked | checked |
| attack event count | contiguous positive runs | 14 | 14 | 14 |
| detected event count / Recall | event overlap summary | stored | stored | stored |
| normal exposure seconds | strict label-0 rows | 51,019 | 51,019 | 51,019 |
| normal false episodes / FAR | episode numerator and hourly rate | stored | stored | stored |
| total alarm episodes | all grouped alarm intervals | 46 | 626 | 49 / 143 |
| result self-hash / integrity receipt | mutation/report binding | present | present downstream | present |
| source commit/config | producing authority | present | present | present |

The schema does not establish independence, utility, superiority, or generalization.
