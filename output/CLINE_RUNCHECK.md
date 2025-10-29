# Runcheck Audit: jcw-estimator-pro

- **Branch:** `master`
- **Start Time:** 2025-10-29 12:30:35 PM
- **Stop Time:** 2025-10-29 12:31:11 PM
- **Launch Command:** `python web/backend/app.py`

## Endpoint Results

| Method | Path       | Status | Latency (ms) |
|--------|------------|--------|--------------|
| GET    | /          | 200    | 34.0005      |
| GET    | /docs      | 200    | 21.0009      |
| POST   | /estimate  | 422    | 118.0011     |

## Sample Response Excerpt (POST /estimate)

The request failed with a 422 Unprocessable Entity error.

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": [
        "body",
        "area_sf"
      ],
      "msg": "Field required",
      "input": {
        "square_footage": 1000,
        "project_type": "Residential",
        "finish_quality": "Standard ($500/sf)",
        "design_complexity": "Moderate",
        "bedrooms": 0,
        "bathrooms": 0,
        "special_features": []
      }
    }
  ]
}
```

## Summary

**Overall Result: FAIL**

The smoke check failed because the `POST /estimate` endpoint returned a 422 error, indicating a mismatch between the client request and the server's expected schema. The server expected `area_sf` but received `square_footage`.

## Remediation Plan

1.  **Align Models:** Update the Pydantic model in `web/backend/app.py` to accept `square_footage` or update the client payload to send `area_sf`.
2.  **Add Input Validation:** Implement more robust error handling to provide clearer error messages for schema mismatches.
3.  **Update API Documentation:** Ensure the OpenAPI documentation at `/docs` accurately reflects the required request body for all endpoints.
