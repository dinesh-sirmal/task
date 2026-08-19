# Rate Limits & Error Handling

## Rate limits
600 requests/minute per API key, 20 concurrent uploads per account. Exceeding the limit
returns HTTP 429 with a `Retry-After` header (seconds).

## Standard error format
```
{ "error": { "code": "string", "message": "string", "request_id": "string" } }
```

## Common error codes
- `400 validation_error`: malformed request body or missing required field.
- `404 not_found`: resource does not exist or was permanently deleted.
- `409 conflict`: concurrent modification conflict (see versioning doc).
- `500 internal_error`: retry with exponential backoff; include `request_id` when contacting support.
