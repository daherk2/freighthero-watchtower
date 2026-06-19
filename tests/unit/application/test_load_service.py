"""Tests for LoadService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.application.services.load_service import LoadService
from src.application.dto import CreateLoadRequest, CreateLoadResponse, ActiveLoadSummary, StateTransitionSummary
from src.domain.enums import CustomerId, LoadState
from src.domain.exceptions import LoadNotFoundError, InvalidStateTransitionError
from src.domain.models import Load


def make_load(**overrides):
    """Helper to create a Load with all required fields."""
    defaults = dict(
        load_id="load-1",
        customer_id=CustomerId.CUSTOMER_A,
        external_load_id="ext-1",
        current_state=LoadState.DISPATCHED,
        load_data={"origin": "A", "destination": "B"},
    )
    defaults.update(overrides)
    return Load(**defaults)


@pytest.fixture
def mock_load_repo():
    return AsyncMock()


@pytest.fixture
def mock_event_repo():
    return AsyncMock()


@pytest.fixture
def sample_load():
    return make_load()


class TestLoadServiceCreateLoad:
    @pytest.mark.asyncio
    async def test_create_load_basic(self, mock_load_repo, mock_event_repo):
        saved_load = make_load(load_id="load-new", created_at=datetime.now(timezone.utc).isoformat())
        mock_load_repo.save = AsyncMock(return_value=saved_load)

        service = LoadService(load_repo=mock_load_repo, event_repo=mock_event_repo)
        request = CreateLoadRequest(customer_id="customer_a", load_data={"origin": "A"})

        result = await service.create_load(request)
        assert isinstance(result, CreateLoadResponse)
        assert result.customer_id == CustomerId.CUSTOMER_A
        mock_load_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_load_with_custom_id(self, mock_load_repo, mock_event_repo):
        saved_load = make_load(load_id="my-custom-id", customer_id=CustomerId.CUSTOMER_B, created_at=datetime.now(timezone.utc).isoformat())
        mock_load_repo.save = AsyncMock(return_value=saved_load)

        service = LoadService(load_repo=mock_load_repo, event_repo=mock_event_repo)
        request = CreateLoadRequest(load_id="my-custom-id", customer_id="customer_b", load_data={})

        result = await service.create_load(request)
        assert result.load_id == "my-custom-id"

    @pytest.mark.asyncio
    async def test_create_load_without_pipeline(self, mock_load_repo, mock_event_repo):
        saved_load = make_load(created_at=datetime.now(timezone.utc).isoformat())
        mock_load_repo.save = AsyncMock(return_value=saved_load)

        service = LoadService(load_repo=mock_load_repo, event_repo=mock_event_repo)
        request = CreateLoadRequest(customer_id="customer_a", load_data={}, run_pipeline=False)

        result = await service.create_load(request)
        assert result.pipeline_triggered is False
        assert result.pipeline_status is None


class TestLoadServiceGetLoad:
    @pytest.mark.asyncio
    async def test_get_load(self, mock_load_repo, sample_load):
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)

        service = LoadService(load_repo=mock_load_repo)
        result = await service.get_load("load-1")

        assert result["load_id"] == "load-1"
        assert result["customer_id"] == "customer_a"
        assert result["current_state"] == "dispatched"

    @pytest.mark.asyncio
    async def test_get_load_not_found(self, mock_load_repo):
        mock_load_repo.get_by_id = AsyncMock(side_effect=LoadNotFoundError("load-missing"))

        service = LoadService(load_repo=mock_load_repo)
        with pytest.raises(LoadNotFoundError):
            await service.get_load("load-missing")


class TestLoadServiceGetActiveLoads:
    @pytest.mark.asyncio
    async def test_get_active_loads(self, mock_load_repo):
        loads = [
            make_load(load_id="load-1"),
            make_load(load_id="load-2", customer_id=CustomerId.CUSTOMER_B, current_state=LoadState.ON_ROUTE_TO_DELIVERY),
        ]
        mock_load_repo.get_active_loads = AsyncMock(return_value=loads)

        service = LoadService(load_repo=mock_load_repo)
        result = await service.get_active_loads()

        assert len(result) == 2
        assert all(isinstance(r, ActiveLoadSummary) for r in result)

    @pytest.mark.asyncio
    async def test_get_active_loads_empty(self, mock_load_repo):
        mock_load_repo.get_active_loads = AsyncMock(return_value=[])

        service = LoadService(load_repo=mock_load_repo)
        result = await service.get_active_loads()
        assert result == []


class TestLoadServiceTransitionState:
    @pytest.mark.asyncio
    async def test_transition_state(self, mock_load_repo, sample_load):
        mock_load_repo.get_by_id = AsyncMock(return_value=sample_load)
        mock_load_repo.save = AsyncMock(return_value=sample_load)

        service = LoadService(load_repo=mock_load_repo)
        result = await service.transition_state("load-1", LoadState.ON_ROUTE_TO_DELIVERY)

        assert isinstance(result, StateTransitionSummary)
        assert result.load_id == "load-1"
        assert result.from_state == LoadState.DISPATCHED
        assert result.to_state == LoadState.ON_ROUTE_TO_DELIVERY

    @pytest.mark.asyncio
    async def test_transition_state_load_not_found(self, mock_load_repo):
        mock_load_repo.get_by_id = AsyncMock(side_effect=LoadNotFoundError("load-missing"))

        service = LoadService(load_repo=mock_load_repo)
        with pytest.raises(LoadNotFoundError):
            await service.transition_state("load-missing", LoadState.ON_ROUTE_TO_DELIVERY)


class TestLoadServiceLoadToDict:
    def test_load_to_dict(self, mock_load_repo, sample_load):
        service = LoadService(load_repo=mock_load_repo)
        result = service._load_to_dict(sample_load)

        assert result["load_id"] == "load-1"
        assert result["customer_id"] == "customer_a"
        assert result["current_state"] == "dispatched"
        assert result["external_load_id"] == "ext-1"