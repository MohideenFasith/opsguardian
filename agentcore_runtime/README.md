# AgentCore runtime payload

The runtime accepts either:

```json
{"prompt":"Investigate the bundled customer_id schema drift and validate the safest repair."}
```

or:

```json
{"anomaly":{"dataset":"crm.customer_export","field":"customer_id","expected_type":"INTEGER","observed_type":"STRING","first_bad_version":"crm_export_v42","sample_new_values":["100482","C-100483"]}}
```

The runtime exposes only evidence/lineage/sandbox tools to the model. Production writes remain outside the model boundary.
