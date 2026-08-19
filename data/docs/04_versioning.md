# File Versioning

Every write to a file creates a new version. Versions are immutable and retained for
90 days on the free tier, unlimited on paid tiers.

## List versions
GET `/v1/files/{file_id}/versions` returns an array of `{version_id, size, created_at, author}`.

## Restore a version
POST `/v1/files/{file_id}/versions/{version_id}/restore` makes that version the current one;
this itself creates a new version rather than overwriting history.

## Conflict handling
If two clients write to the same file concurrently, CloudSync uses last-write-wins at the
API layer and creates a conflicted copy named `<filename> (conflicted copy).ext` for the loser.
