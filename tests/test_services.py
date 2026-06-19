"""Unit tests for application services."""

import uuid
from datetime import datetime, timezone

import pytest

from src.domain.enums import (
    CustomerId,
    EventType,
    LoadState,
    SOPBranch,
    ConfirmDeliveryBranch,
)
from src.application.services.customer_resolver import CustomerBehaviorResolver
from src.application.services.sop_compiler import SOPCompiler


class TestCustomerBehaviorResolver:
    """Tests for CustomerBehaviorResolver."""

    def setup_method(self):
        self.resolver = CustomerBehaviorResolver()

    @pytest.mark.asyncio
    async def test_get_config_customer_a(self):
        """Test getting config for customer_a."""
        config = await self.resolver.get_config(CustomerId.CUSTOMER_A)
        assert config.customer_id == CustomerId.CUSTOMER_A
        assert config.escalation_channel == "email"
        assert config.pod_validation_type == "automatic"
        assert config.delivery_geofence_radius_miles == 1
        assert config.eta_followup_timer_minutes == 30

    @pytest.mark.asyncio
    async def test_get_config_customer_b(self):
        """Test getting config for customer_b."""
        config = await self.resolver.get_config(CustomerId.CUSTOMER_B)
        assert config.customer_id == CustomerId.CUSTOMER_B
        assert config.escalation_channel == "slack"
        assert config.pod_validation_type == "human_review"
        assert config.delivery_geofence_radius_miles == 2
        assert config.eta_followup_timer_minutes == 60

    @pytest.mark.asyncio
    async def test_get_config_customer_c(self):
        """Test getting config for customer_c."""
        config = await self.resolver.get_config(CustomerId.CUSTOMER_C)
        assert config.customer_id == CustomerId.CUSTOMER_C
        assert config.escalation_channel == "email_and_slack"
        assert config.pod_validation_type == "automatic"
        assert config.delivery_geofence_radius_miles == 3
        assert config.eta_followup_timer_minutes == 45

    @pytest.mark.asyncio
    async def test_get_all_configs(self):
        """Test getting all customer configs."""
        configs = await self.resolver.get_all_configs()
        assert len(configs) == 3
        assert CustomerId.CUSTOMER_A in configs
        assert CustomerId.CUSTOMER_B in configs
        assert CustomerId.CUSTOMER_C in configs

    def test_get_geofence_radius(self):
        """Test getting geofence radius for each customer."""
        radius_a = self.resolver.get_geofence_radius(CustomerId.CUSTOMER_A)
        radius_b = self.resolver.get_geofence_radius(CustomerId.CUSTOMER_B)
        radius_c = self.resolver.get_geofence_radius(CustomerId.CUSTOMER_C)

        assert radius_a == 1
        assert radius_b == 2
        assert radius_c == 3

    def test_get_eta_timer_minutes(self):
        """Test getting ETA timer for each customer."""
        timer_a = self.resolver.get_eta_timer_minutes(CustomerId.CUSTOMER_A)
        timer_b = self.resolver.get_eta_timer_minutes(CustomerId.CUSTOMER_B)
        timer_c = self.resolver.get_eta_timer_minutes(CustomerId.CUSTOMER_C)

        assert timer_a == 30
        assert timer_b == 60
        assert timer_c == 45


class TestSOPCompiler:
    """Tests for SOPCompiler."""

    def setup_method(self):
        self.resolver = CustomerBehaviorResolver()
        self.compiler = SOPCompiler(self.resolver)

    @pytest.mark.asyncio
    async def test_get_base_sop_eta_checkpoint(self):
        """Test getting base SOP for ETA checkpoint."""
        sop = await self.compiler.get_base_sop("delivery_eta_checkpoint")
        assert "ETA Checkpoint" in sop
        assert "Tracking Ping" in sop
        assert "Arrival" in sop

    @pytest.mark.asyncio
    async def test_get_base_sop_confirm_delivery(self):
        """Test getting base SOP for confirm delivery."""
        sop = await self.compiler.get_base_sop("confirm_delivery")
        assert "Confirm Delivery" in sop
        assert "POD" in sop
        assert "Lumper" in sop

    @pytest.mark.asyncio
    async def test_get_compiled_sop_includes_customer_rules(self):
        """Test that compiled SOP includes customer-specific rules."""
        sop = await self.compiler.get_sop("delivery_eta_checkpoint", CustomerId.CUSTOMER_A)
        assert "Customer-Specific Rules" in sop
        assert "CUSTOMER_A" in sop
        assert "escalation channel" in sop.lower()

    @pytest.mark.asyncio
    async def test_get_compiled_sop_customer_b(self):
        """Test compiled SOP for customer_b."""
        sop = await self.compiler.get_sop("confirm_delivery", CustomerId.CUSTOMER_B)
        assert "CUSTOMER_B" in sop
        assert "human_review" in sop  # POD validation type

    @pytest.mark.asyncio
    async def test_get_unknown_sop(self):
        """Test getting an unknown SOP returns empty string."""
        sop = await self.compiler.get_base_sop("unknown_workflow")
        assert sop == ""