# API Rate Limits

The API returns HTTP 429 when a workspace exceeds its request limit. Clients should use exponential backoff with jitter and avoid retry storms.

Enterprise customers can request higher limits by sharing current throughput, expected peak traffic, and the business impact of throttling.
