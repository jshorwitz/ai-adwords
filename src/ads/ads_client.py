"""Google Ads API client factory and authentication."""

import logging
from collections.abc import Callable
from typing import Any

from google.ads.googleads.client import (  # type: ignore
    GoogleAdsClient as BaseGoogleAdsClient,
)
from google.ads.googleads.errors import GoogleAdsException  # type: ignore
from google.api_core import retry
from google.api_core.exceptions import GoogleAPICallError, RetryError

logger = logging.getLogger(__name__)


class _MockGoogleAdsClient:
    """Very small mock of Google Ads client for local mock mode.

    Provides just enough surface for list-accessible customers and for code that reads
    `login_customer_id` and `get_service(...)`.
    """

    def __init__(self, login_customer_id: str | None = None):
        self.login_customer_id = login_customer_id or "0000000000"

    def get_service(self, name: str):
        if name == "CustomerService":

            class _CustomerService:
                def list_accessible_customers(self):
                    class _Resp:
                        resource_names = [
                            "customers/1234567890",
                            "customers/2345678901",
                        ]

                    return _Resp()

            return _CustomerService()
        if name == "GoogleAdsService":

            class _GoogleAdsService:
                def search_stream(self, request=None):
                    return []

                def search(self, customer_id=None, query=None):
                    return []

            return _GoogleAdsService()
        raise ValueError(f"Unsupported mock service: {name}")


class GoogleAdsClientFactory:
    """Factory for creating authenticated Google Ads API clients."""

    def __init__(
        self,
        developer_token: str,
        refresh_token: str,
        client_id: str,
        client_secret: str,
        login_customer_id: str | None = None,
    ):
        """Initialize Google Ads client factory.

        Args:
            developer_token: Google Ads API developer token
            refresh_token: OAuth refresh token
            client_id: OAuth client ID
            client_secret: OAuth client secret
            login_customer_id: MCC customer ID (digits only)
        """
        self.developer_token = developer_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.login_customer_id = self._validate_customer_id(login_customer_id)

    def _validate_customer_id(self, customer_id: str | None) -> str | None:
        """Validate customer ID format (digits only)."""
        if customer_id is None:
            return None

        # Remove any dashes or spaces and validate digits only
        clean_id = customer_id.replace("-", "").replace(" ", "")
        if not clean_id.isdigit():
            raise ValueError(f"Customer ID must contain only digits: {customer_id}")

        return clean_id

    def create_client(self) -> BaseGoogleAdsClient:
        """Create authenticated Google Ads client with retry configuration.

        Defaults to REST transport to avoid gRPC issues in constrained environments.
        Set GOOGLE_ADS_USE_GRPC=true to force gRPC.
        """
        import os

        # Force REST transport to avoid GRPC issues
        os.environ["GOOGLE_ADS_USE_GRPC"] = "false"

        config = {
            "developer_token": self.developer_token,
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "use_proto_plus": True,
            "http_proxy": None,  # Ensure no proxy interference
            "https_proxy": None,
        }

        if self.login_customer_id:
            config["login_customer_id"] = self.login_customer_id

        return BaseGoogleAdsClient.load_from_dict(config)

    def get_retry_config(self) -> retry.Retry:
        """Get retry configuration with exponential backoff."""
        return retry.Retry(
            initial=1.0,  # Initial delay
            maximum=60.0,  # Maximum delay
            multiplier=2.0,  # Exponential backoff multiplier
            predicate=retry.if_exception_type(
                GoogleAdsException,
                GoogleAPICallError,
                RetryError,
            ),
            deadline=300.0,  # Total timeout (5 minutes)
        )


class GoogleAdsService:
    """High-level service wrapper for Google Ads operations."""

    def __init__(self, client_factory: GoogleAdsClientFactory):
        """Initialize service with client factory."""
        self.client_factory = client_factory
        self._client = None

    @property
    def client(self) -> BaseGoogleAdsClient:
        """Lazy-loaded Google Ads client."""
        if self._client is None:
            self._client = self.client_factory.create_client()
        return self._client

    def execute_with_retry(
        self, operation: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute operation with retry logic."""
        retry_config = self.client_factory.get_retry_config()

        @retry_config
        def _execute() -> Any:
            try:
                return operation(*args, **kwargs)
            except GoogleAdsException as ex:
                logger.error(f"Google Ads API error: {ex}")
                for error in ex.failure.errors:
                    logger.error(f"Error: {error.error_code.name}: {error.message}")
                raise
            except Exception as ex:
                logger.error(f"Unexpected error: {ex}")
                raise

        return _execute()

    def validate_credentials(self) -> bool:
        """Validate API credentials without making actual calls."""
        try:
            # Just create the client to validate configuration
            _ = self.client
            return True
        except Exception as ex:
            logger.error(f"Credential validation failed: {ex}")
            return False


def create_client_from_env() -> GoogleAdsService:
    """Create client from environment variables or return a mock client.

    If ADS_USE_MOCK=1, returns a minimal mock client so the app can run without
    Google Ads credentials or network access.
    """
    import os

    from dotenv import load_dotenv

    load_dotenv()

    if os.getenv("ADS_USE_MOCK") == "1":
        logger.warning("ADS_USE_MOCK=1: using mock Google Ads client (no API calls)")

        # Build a tiny shim so callers can keep using the same interface
        class _MockFactory(GoogleAdsClientFactory):
            def __init__(self):
                super().__init__(
                    developer_token="mock",
                    refresh_token="mock",
                    client_id="mock",
                    client_secret="mock",
                    login_customer_id=os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
                )

            def create_client(self):
                return _MockGoogleAdsClient(login_customer_id=self.login_customer_id)

        return GoogleAdsService(_MockFactory())

    required_vars = [
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")

    factory = GoogleAdsClientFactory(
        developer_token=os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
        refresh_token=os.getenv("GOOGLE_ADS_REFRESH_TOKEN", ""),
        client_id=os.getenv("GOOGLE_ADS_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_ADS_CLIENT_SECRET", ""),
        login_customer_id=os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
    )

    return GoogleAdsService(factory)
