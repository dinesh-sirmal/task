# Authentication

CloudSync uses OAuth 2.0 client-credentials flow for server-to-server integrations.

## Getting a token
POST `/v1/oauth/token` with `client_id`, `client_secret`, and `grant_type=client_credentials`.
The response contains an `access_token` valid for 3600 seconds and a `refresh_token`.

## Refreshing a token
POST `/v1/oauth/token` with `grant_type=refresh_token` and the `refresh_token` value.

## Errors
- 401 `invalid_token`: token expired or malformed, re-authenticate.
- 403 `insufficient_scope`: the token does not have the required scope for the endpoint.
