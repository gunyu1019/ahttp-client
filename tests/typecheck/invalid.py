from ahttp_client.retry import RetryConfig, retry

retry("three")  # type: ignore[arg-type]
retry(backoff_factor="slow")  # type: ignore[arg-type]
retry(retry_on=ValueError())  # type: ignore[arg-type]
retry(max_delay="never")  # type: ignore[arg-type]
retry(retry_unsafe=1)  # type: ignore[arg-type]

RetryConfig(max_retries="three")  # type: ignore[arg-type]
RetryConfig(backoff_factor="slow")  # type: ignore[arg-type]
RetryConfig(retry_on=(ValueError(),))  # type: ignore[arg-type]
RetryConfig(max_delay="never")  # type: ignore[arg-type]
RetryConfig(retry_unsafe=1)  # type: ignore[arg-type]
