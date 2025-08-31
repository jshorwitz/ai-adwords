"""Unit tests for ads_client module."""

from unittest.mock import Mock, patch

import pytest

from src.ads.ads_client import (
    GoogleAdsClientFactory,
    GoogleAdsService,
    create_client_from_env,
)


class TestGoogleAdsClientFactory:
    """Test GoogleAdsClientFactory."""

    def test_init_with_valid_customer_id(self):
        """Test initialization with valid customer ID."""
        factory = GoogleAdsClientFactory(
            developer_token="dev_token",
            refresh_token="refresh_token",
            client_id="client_id",
            client_secret="client_secret",
            login_customer_id="1234567890",
        )

        assert factory.developer_token == "dev_token"
        assert factory.refresh_token == "refresh_token"
        assert factory.client_id == "client_id"
        assert factory.client_secret == "client_secret"
        assert factory.login_customer_id == "1234567890"

    def test_customer_id_validation_removes_dashes(self):
        """Test customer ID validation removes dashes."""
        factory = GoogleAdsClientFactory(
            developer_token="dev_token",
            refresh_token="refresh_token",
            client_id="client_id",
            client_secret="client_secret",
            login_customer_id="123-456-7890",
        )

        assert factory.login_customer_id == "1234567890"

    def test_customer_id_validation_invalid_format(self):
        """Test customer ID validation with invalid format."""
        with pytest.raises(ValueError, match="Customer ID must contain only digits"):
            GoogleAdsClientFactory(
                developer_token="dev_token",
                refresh_token="refresh_token",
                client_id="client_id",
                client_secret="client_secret",
                login_customer_id="123abc",
            )

    def test_customer_id_none_allowed(self):
        """Test that None customer ID is allowed."""
        factory = GoogleAdsClientFactory(
            developer_token="dev_token",
            refresh_token="refresh_token",
            client_id="client_id",
            client_secret="client_secret",
            login_customer_id=None,
        )

        assert factory.login_customer_id is None

    @patch("src.ads.ads_client.BaseGoogleAdsClient.load_from_dict")
    def test_create_client_with_login_customer_id(self, mock_load):
        """Test client creation includes login_customer_id."""
        factory = GoogleAdsClientFactory(
            developer_token="dev_token",
            refresh_token="refresh_token",
            client_id="client_id",
            client_secret="client_secret",
            login_customer_id="1234567890",
        )

        factory.create_client()

        mock_load.assert_called_once()
        config = mock_load.call_args[0][0]

        assert config["developer_token"] == "dev_token"
        assert config["refresh_token"] == "refresh_token"
        assert config["client_id"] == "client_id"
        assert config["client_secret"] == "client_secret"
        assert config["login_customer_id"] == "1234567890"
        assert config["use_proto_plus"] is True

    @patch("src.ads.ads_client.BaseGoogleAdsClient.load_from_dict")
    def test_create_client_without_login_customer_id(self, mock_load):
        """Test client creation without login_customer_id."""
        factory = GoogleAdsClientFactory(
            developer_token="dev_token",
            refresh_token="refresh_token",
            client_id="client_id",
            client_secret="client_secret",
            login_customer_id=None,
        )

        factory.create_client()

        mock_load.assert_called_once()
        config = mock_load.call_args[0][0]

        assert "login_customer_id" not in config

    def test_retry_config(self):
        """Test retry configuration parameters."""
        factory = GoogleAdsClientFactory(
            developer_token="dev_token",
            refresh_token="refresh_token",
            client_id="client_id",
            client_secret="client_secret",
        )

        retry_config = factory.get_retry_config()

        assert retry_config._initial == 1.0
        assert retry_config._maximum == 60.0
        assert retry_config._multiplier == 2.0
        assert retry_config._deadline == 300.0


class TestGoogleAdsService:
    """Test GoogleAdsService."""

    def test_init(self):
        """Test service initialization."""
        factory = Mock()
        service = GoogleAdsService(factory)

        assert service.client_factory == factory
        assert service._client is None

    @patch("src.ads.ads_client.BaseGoogleAdsClient.load_from_dict")
    def test_client_lazy_loading(self, mock_load):
        """Test client lazy loading."""
        mock_client = Mock()
        mock_load.return_value = mock_client

        factory = GoogleAdsClientFactory(
            developer_token="dev_token",
            refresh_token="refresh_token",
            client_id="client_id",
            client_secret="client_secret",
        )

        service = GoogleAdsService(factory)

        # First access should create client
        client1 = service.client
        assert client1 == mock_client
        mock_load.assert_called_once()

        # Second access should reuse client
        client2 = service.client
        assert client2 == mock_client
        assert mock_load.call_count == 1  # Not called again

    def test_validate_credentials_success(self):
        """Test successful credential validation."""
        factory = Mock()
        mock_client = Mock()
        factory.create_client.return_value = mock_client

        service = GoogleAdsService(factory)

        assert service.validate_credentials() is True

    def test_validate_credentials_failure(self):
        """Test credential validation failure."""
        factory = Mock()
        factory.create_client.side_effect = Exception("Invalid credentials")

        service = GoogleAdsService(factory)

        assert service.validate_credentials() is False


class TestCreateClientFromEnv:
    """Test create_client_from_env function."""

    @patch.dict(
        "os.environ",
        {
            "GOOGLE_ADS_DEVELOPER_TOKEN": "dev_token",
            "GOOGLE_ADS_REFRESH_TOKEN": "refresh_token",
            "GOOGLE_ADS_CLIENT_ID": "client_id",
            "GOOGLE_ADS_CLIENT_SECRET": "client_secret",
            "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "1234567890",
        },
    )
    @patch("dotenv.load_dotenv")
    def test_create_client_from_env_success(self, mock_load_dotenv):
        """Test successful client creation from environment."""
        service = create_client_from_env()

        assert isinstance(service, GoogleAdsService)
        assert service.client_factory.developer_token == "dev_token"
        assert service.client_factory.login_customer_id == "1234567890"
        mock_load_dotenv.assert_called_once()

    @patch.dict(
        "os.environ",
        {
            "GOOGLE_ADS_DEVELOPER_TOKEN": "dev_token",
            # Missing GOOGLE_ADS_REFRESH_TOKEN
            "GOOGLE_ADS_CLIENT_ID": "client_id",
            "GOOGLE_ADS_CLIENT_SECRET": "client_secret",
        },
        clear=True,
    )
    @patch("dotenv.load_dotenv")
    def test_create_client_from_env_missing_vars(self, mock_load_dotenv):
        """Test client creation with missing environment variables."""
        with pytest.raises(ValueError, match="Missing required environment variables"):
            create_client_from_env()
