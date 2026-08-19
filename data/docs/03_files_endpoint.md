# Files Endpoint

## Upload a file
POST `/v1/files` (multipart/form-data), fields: `file`, `folder_id` (optional).
Max file size: 5 GB. Returns a `file_id`, `checksum`, and `created_at`.

## Download a file
GET `/v1/files/{file_id}/content` streams the raw bytes. Supports HTTP Range headers
for partial/resumable downloads.

## Delete a file
DELETE `/v1/files/{file_id}` moves the file to trash; permanent deletion happens after
30 days unless purged with `?permanent=true`.

## List files
GET `/v1/files?folder_id=&page=&page_size=` returns paginated results, max page_size 100.
