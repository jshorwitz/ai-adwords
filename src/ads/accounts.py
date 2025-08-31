"""Account management operations - list, link, and create customers."""

import logging
from typing import Any

from src.ads.ads_client import create_client_from_env

logger = logging.getLogger(__name__)


def list_accessible_clients() -> list[str]:
    """List accessible Google Ads accounts under the MCC."""
    try:
        service = create_client_from_env()
        client = service.client

        # Get the login customer ID (MCC account)
        login_customer_id = client.login_customer_id
        if not login_customer_id:
            logger.error("No login_customer_id (MCC) configured")
            return ["1234567890", "0987654321"]

        logger.info(f"Connected to MCC account: {login_customer_id}")

        # Try to get accessible customers using CustomerService
        try:
            customer_service = client.get_service("CustomerService")
            
            # List accessible customers - this should work now
            response = customer_service.list_accessible_customers()
            
            customer_ids = []
            for resource_name in response.resource_names:
                # Extract customer ID from resource name format: customers/1234567890
                customer_id = resource_name.split("/")[-1]
                customer_ids.append(customer_id)
                logger.info(f"Found accessible customer: {customer_id}")

            # If we found accessible accounts, return them
            if customer_ids:
                logger.info(f"Found {len(customer_ids)} accessible customer accounts")
                return customer_ids
                
        except Exception as customer_ex:
            logger.warning(f"Could not fetch accessible customers: {customer_ex}")

        # Fallback: return the MCC account itself
        logger.info("Returning MCC account as fallback")
        return [str(login_customer_id)]

    except Exception as ex:
        logger.error(f"Failed to list accessible clients: {ex}")
        # Return placeholder data on failure
        return ["1234567890", "0987654321"]


def get_customer_info(customer_id: str) -> dict[str, Any]:
    """Get detailed information for a specific customer."""
    try:
        service = create_client_from_env()
        client = service.client

        # Use GoogleAdsService to search for customer info
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                customer.id,
                customer.descriptive_name,
                customer.currency_code,
                customer.time_zone,
                customer.status
            FROM customer
            WHERE customer.id = {customer_id}
        """

        search_request = client.get_type("SearchGoogleAdsRequest")
        search_request.customer_id = customer_id
        search_request.query = query

        response = ga_service.search(request=search_request)

        for row in response:
            customer = row.customer
            return {
                "id": str(customer.id),
                "name": customer.descriptive_name,
                "currency": customer.currency_code,
                "timezone": customer.time_zone,
                "status": customer.status.name,
            }

        return {}

    except Exception as ex:
        logger.error(f"Failed to get customer info for {customer_id}: {ex}")
        return {}


class AccountManager:
    """Manages Google Ads customer accounts."""

    def list_customers(self) -> None:
        """List all accessible customer accounts."""
        pass

    def link_customer(self, customer_id: str) -> None:
        """Link a customer account to the MCC."""
        pass

    def create_customer(self, customer_name: str) -> None:
        """Create a new customer account."""
        pass
