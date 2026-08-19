# Sharing & Permissions

## Create a share link
POST `/v1/shares` with `resource_id`, `resource_type` (`file` or `folder`), and `permission`
(`view`, `comment`, or `edit`). Optional `expires_at` (ISO 8601) and `password`.

## Permission levels
- `view`: read-only, no downloads unless `allow_download=true`.
- `comment`: view plus the ability to leave comments.
- `edit`: full read/write access to the shared resource.

## Revoking access
DELETE `/v1/shares/{share_id}` immediately invalidates the link for all holders.
