"""SOP Compiler and Loader service.

Compiles SOP content from the specification documents, combining
base SOPs with customer-specific modifications to produce the
final agent instructions.
"""

from src.domain.enums import CustomerId
from src.domain.value_objects import CustomerBehaviorConfig


# Base SOP content for ETA Checkpoint workflow
ETA_CHECKPOINT_SOP = """# SOP: On Route to Delivery / ETA Checkpoint

## Purpose
Monitor delivery ETA, tracking, arrival, driver questions, and operational exceptions while a driver is en route.

## Operating Principles
- Apply the relevant customer expectations for this load.
- Match the driver's inbound channel for driver-facing replies unless the customer workflow says otherwise.
- Keep driver-facing messages short, specific, and operational.
- Do not invent missing load information.
- Ignore broker-originated inbound messages in this challenge.
- Leave a clear reason for the selected branch.

## Event Routing
1. If the event is a tracking ping, follow Tracking Ping Handling.
2. If the event is inbound communication, identify the sender, channel, message content, and attachments.
3. If the sender is the broker, follow Broker Messages.
4. If the message indicates arrival, follow Arrival Confirmation.
5. If the message provides ETA, follow Driver Provides ETA.
6. If the message asks for load information, follow Load Information Question.
7. If the message reports operational trouble, follow Operational Issue.
8. Otherwise, acknowledge only when the driver clearly expects a response.

## Branch Details

### Tracking Ping Handling
1. Determine whether the ping is fresh based on its timestamp.
2. Compare the provided distance to delivery against the customer's delivery geofence.
3. If tracking is stale, keep the load on route to delivery and continue the customer's ETA follow-up process.
4. If tracking is fresh but outside the geofence, keep the load on route to delivery.
5. If there are three consecutive fresh pings inside the delivery geofence, treat the driver as arrived at delivery and begin confirm delivery handling.

### Arrival Confirmation
1. Treat the load as at delivery.
2. Stop ETA follow-up pressure for the on-route workflow.
3. Begin confirm delivery handling.

### Driver Provides ETA
1. Interpret the ETA using the delivery stop timezone.
2. Check whether the ETA is plausible for the delivery stop and appointment.
3. If the ETA is usable, record it, acknowledge the update on the same channel, and continue follow-up according to the customer's ETA timer.
4. If the ETA is ambiguous, ask one short clarification question when the driver can reasonably answer it.
5. If the ETA indicates a meaningful service risk, treat it as a delivery delay and make it visible to the operations team according to the customer workflow.

### Load Information Question
1. Look for the requested information in the known load data.
2. If the information is available, reply on the same channel with only the requested information.
3. If the information is missing, follow the customer's missing-information workflow for acknowledgment, human follow-up, and any required visibility.

### Operational Issue
1. Treat the message as an operational exception that needs operations-team attention.
2. Use the most specific issue category that fits the message.
3. If the driver sent the message by SMS, acknowledge briefly that the team will review.
4. Do not give long troubleshooting advice.

### Broker Messages
1. Do not reply.
2. Do not process attachments or delivery updates from the broker message.
3. Record the reason for taking no action.

### No Action
1. Take no external action.
2. Record the reason for no action for later review.
"""

# Base SOP content for Confirm Delivery workflow
CONFIRM_DELIVERY_SOP = """# SOP: Confirm Delivery

## Purpose
Confirm unloading, collect or validate Proof of Delivery, handle lumper receipts when relevant, and escalate only when customer expectations require human review or visibility.

## Operating Principles
- Apply the relevant customer expectations for this load.
- Match the inbound channel when replying to a driver, dispatcher, or carrier.
- Keep driver-facing messages short and operational.
- Do not assume an attachment is POD unless it has been classified as POD or the input is explicitly trusted.
- Do not ask for POD again when valid POD was already received in the same event.
- Do not approve lumper or detention payment.
- Ignore broker-originated inbound messages in this challenge.
- Leave a clear reason for the selected branch, attachment classification, and outcome.

## Event Routing
1. If the sender is the broker, follow Broker Messages.
2. If the message contains attachments, follow Attachment Handling.
3. If the sender says unloading started but is not finished, follow Unloading Started.
4. If the sender says unloading has not started, follow Unloading Not Started.
5. If the sender confirms unloaded, empty, delivered, or done without POD, follow Delivery Confirmed Without POD.
6. If the sender asks load-information questions, use the matching behavior from the ETA checkpoint SOP.
7. If the sender reports a delivery-impacting problem, follow Operational Issue.
8. Otherwise, take no action or send a short acknowledgment only if the driver clearly expects a response.

## Branch Details

### First Arrival Contact
1. Follow the customer's first-arrival acknowledgement and delivery-status follow-up workflow.
2. Do not mention detention unless the driver asked about it.

### Attachment Handling - POD Document
1. Follow the customer's POD receipt acknowledgement, validation, status transition, visibility, and follow-up rules.

### Attachment Handling - Lumper Receipt
1. Record that a lumper receipt was received.
2. Follow the customer's lumper receipt review and visibility rules.
3. If POD is also present, handle POD first and avoid duplicate delivery-state changes.
4. Do not approve reimbursement.

### Attachment Handling - Other or Unreadable
1. If the message suggests delivery is complete, ask for a clear POD.
2. If delivery status is unclear, ask for unloading status.
3. Do not treat the load as POD collected.

### Unloading Started
1. Thank the sender and ask them to send POD when unloaded.
2. Continue delivery-status follow-up.
3. Follow the customer's visibility rules for this status.

### Unloading Not Started
1. Acknowledge and ask for an update when unloading starts or finishes.
2. Do not treat unrelated attachments as POD when the text clearly says unloading has not started.
3. Continue delivery-status follow-up.

### Delivery Confirmed Without POD
1. Treat the load as delivered or likely delivered.
2. Ask for POD.
3. Continue POD follow-up.
4. Follow the customer's visibility rules for this scenario.

### Broker Messages
1. Do not reply.
2. Do not process attachments or delivery updates from the broker message.
3. Record the reason for taking no action.

### Operational Issue
1. Treat the message as an operational exception that needs operations-team attention.
2. Acknowledge briefly if the sender is a driver, dispatcher, or carrier and clearly expects a response.
3. Do not treat the load as delivered or POD collected unless there is a separate clear delivery or POD signal.

## Completion Criteria
The confirm delivery workflow is complete when one of these is true:
- POD is collected;
- delivery is confirmed and any required human document review is open.
"""


class SOPCompiler:
    """Compiles SOP content by combining base SOPs with customer-specific modifications.

    This service takes the base SOP content and injects customer-specific
    behavior rules to produce the final agent instructions. This approach
    avoids hardcoding customer differences in one-off branches.
    """

    def __init__(self, customer_resolver=None):
        self._customer_resolver = customer_resolver
        self._base_sops = {
            "delivery_eta_checkpoint": ETA_CHECKPOINT_SOP,
            "confirm_delivery": CONFIRM_DELIVERY_SOP,
        }

    async def get_sop(self, workflow: str, customer_id: CustomerId) -> str:
        """Get compiled SOP content for a workflow and customer.

        Combines the base SOP with customer-specific rules to produce
        the final agent instructions.

        Args:
            workflow: The workflow type (delivery_eta_checkpoint or confirm_delivery).
            customer_id: The customer identifier.

        Returns:
            Compiled SOP content with customer-specific rules injected.
        """
        base_sop = self._base_sops.get(workflow, "")
        if not base_sop:
            return base_sop

        if self._customer_resolver is None:
            return base_sop

        config = await self._customer_resolver.get_config(customer_id)
        customer_section = self._compile_customer_section(config)

        return f"{base_sop}\n\n## Customer-Specific Rules ({config.customer_id})\n\n{customer_section}"

    async def get_base_sop(self, workflow: str) -> str:
        """Get base SOP content without customer modifications."""
        return self._base_sops.get(workflow, "")

    def _compile_customer_section(self, config: CustomerBehaviorConfig) -> str:
        """Compile customer-specific rules section.

        This method generates a declarative rules section that the agent
        can use to make customer-specific decisions without hardcoded branches.
        """
        rules = [
            f"- Escalation channel: {config.escalation_channel}",
            f"- Missing load info action: {config.missing_load_info_action}",
            f"- POD validation type: {config.pod_validation_type}",
            f"- POD received visibility: {config.pod_received_visibility}",
            f"- Delivered without POD visibility: {config.delivered_without_pod_visibility}",
            f"- Delivery geofence radius: {config.delivery_geofence_radius_miles} mile(s)",
            f"- ETA follow-up timer: {config.eta_followup_timer_minutes} minutes",
            f"- Lumper receipt handling: {config.lumper_receipt_handling}",
            f"- First arrival message: {config.first_arrival_message}",
        ]
        return "\n".join(rules)