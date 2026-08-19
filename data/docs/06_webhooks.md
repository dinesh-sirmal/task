# Webhooks

CloudSync can notify your server about events in near real time.

## Registering a webhook
POST `/v1/webhooks` with `url`, `events` (array, e.g. `["file.created", "file.deleted"]`),
and `secret` used to sign payloads.

## Verifying signatures
Each webhook request includes an `X-CloudSync-Signature` header: HMAC-SHA256 of the raw
request body using your webhook `secret`. Reject requests where the signature doesn't match.

## Retry policy
Failed deliveries (non-2xx response) are retried with exponential backoff: 1m, 5m, 30m, 2h,
then the webhook is disabled after 5 consecutive failures and an email alert is sent.
