# CloudSync API — Overview

CloudSync is a cloud file-synchronization service. The CloudSync API lets developers
upload, download, share, and version files programmatically. It is organized around
three resources: Files, Folders, and Shares.

Base URL: `https://api.cloudsync.example.com/v1`

All requests must use HTTPS and include an `Authorization: Bearer <token>` header.
Responses are JSON. Rate limit: 600 requests per minute per API key.
