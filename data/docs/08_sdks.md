# Official SDKs

CloudSync provides official SDKs for Python, Node.js, and Go.

- Python: `pip install cloudsync-sdk`, client class `CloudSyncClient(api_key=...)`.
- Node.js: `npm install @cloudsync/sdk`, `new CloudSyncClient({ apiKey })`.
- Go: `go get github.com/cloudsync/sdk-go`.

All SDKs handle token refresh automatically and expose typed methods mirroring the REST
endpoints (e.g. `client.files.upload(path)`, `client.shares.create(...)`).
