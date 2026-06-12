"""Customer behavior resolver service.

Resolves customer-specific behavior configuration based on the
customer expectations matrix defined in the architecture documentation.
"""

from src.domain.enums import CustomerId
from src.domain.value_objects import CustomerBehaviorConfig


# Customer behavior configuration matrix (from docs/artifacts/customer-expectations.md)
CUSTOMER_CONFIGS: dict[CustomerId, CustomerBehaviorConfig] = {
    CustomerId.CUSTOMER_A: CustomerBehaviorConfig(
        customer_id=CustomerId.CUSTOMER_A,
        escalation_channel="email",
        missing_load_info_action="create_task",
        pod_validation_type="automatic",
        pod_received_visibility="notify_escalation_channel",
        delivered_without_pod_visibility="notify_escalation_channel",
        delivery_geofence_radius_miles=1,
        eta_followup_timer_minutes=30,
        lumper_receipt_handling="classify_and_create_review_task",
        first_arrival_message="Ask for unloading status and POD when available.",
    ),
    CustomerId.CUSTOMER_B: CustomerBehaviorConfig(
        customer_id=CustomerId.CUSTOMER_B,
        escalation_channel="slack",
        missing_load_info_action="create_task_and_send_visibility",
        pod_validation_type="human_review",
        pod_received_visibility="no_notification",
        delivered_without_pod_visibility="no_notification",
        delivery_geofence_radius_miles=2,
        eta_followup_timer_minutes=60,
        lumper_receipt_handling="classify_and_create_review_task",
        first_arrival_message="Ask driver to confirm unloading start and send POD when empty.",
    ),
    CustomerId.CUSTOMER_C: CustomerBehaviorConfig(
        customer_id=CustomerId.CUSTOMER_C,
        escalation_channel="email_and_slack",
        missing_load_info_action="create_task",
        pod_validation_type="automatic",
        pod_received_visibility="notify_escalation_channel",
        delivered_without_pod_visibility="notify_escalation_channel",
        delivery_geofence_radius_miles=3,
        eta_followup_timer_minutes=45,
        lumper_receipt_handling="forward_email_if_lumper_else_review_task",
        first_arrival_message="Ask for unloading updates, POD, and any lumper receipt when available.",
    ),
}


class CustomerBehaviorResolver:
    """Resolves customer-specific behavior configuration.

    This service provides declarative, non-hardcoded access to customer
    behavior differences. New customers can be added by extending the
    CUSTOMER_CONFIGS dictionary.
    """

    def __init__(self, configs: dict[CustomerId, CustomerBehaviorConfig] | None = None):
        self._configs = configs or CUSTOMER_CONFIGS

    async def get_config(self, customer_id: CustomerId) -> CustomerBehaviorConfig:
        """Get behavior configuration for a customer.

        Args:
            customer_id: The customer identifier.

        Returns:
            CustomerBehaviorConfig for the customer.

        Raises:
            CustomerConfigNotFoundError: If the customer is not found.
        """
        from src.domain.exceptions import CustomerConfigNotFoundError

        config = self._configs.get(customer_id)
        if config is None:
            raise CustomerConfigNotFoundError(customer_id)
        return config

    async def get_all_configs(self) -> dict[CustomerId, CustomerBehaviorConfig]:
        """Get all customer configurations."""
        return self._configs.copy()

    def get_geofence_radius(self, customer_id: CustomerId) -> int:
        """Get the delivery geofence radius for a customer."""
        return self._configs[customer_id].delivery_geofence_radius_miles

    def get_eta_timer_minutes(self, customer_id: CustomerId) -> int:
        """Get the ETA follow-up timer minutes for a customer."""
        return self._configs[customer_id].eta_followup_timer_minutes

    def get_escalation_channel(self, customer_id: CustomerId) -> str:
        """Get the escalation channel for a customer."""
        return self._configs[customer_id].escalation_channel

    def get_pod_validation_type(self, customer_id: CustomerId) -> str:
        """Get the POD validation type for a customer."""
        return self._configs[customer_id].pod_validation_type

    def get_first_arrival_message(self, customer_id: CustomerId) -> str:
        """Get the first arrival message template for a customer."""
        return self._configs[customer_id].first_arrival_message