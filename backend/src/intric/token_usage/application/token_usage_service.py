from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from intric.roles.permissions import Permission, validate_permissions
from intric.token_usage.domain.token_usage_models import TokenUsageSummary
from intric.token_usage.domain.user_token_usage_models import UserTokenUsageSummary
from intric.token_usage.infrastructure.token_usage_analyzer import TokenUsageAnalyzer
from intric.token_usage.infrastructure.user_token_usage_analyzer import UserTokenUsageAnalyzer
from intric.users.user import UserInDB


class TokenUsageService:
    """Service for analyzing and retrieving token usage data."""

    def __init__(self, user: UserInDB, token_usage_analyzer: TokenUsageAnalyzer, user_token_usage_analyzer: UserTokenUsageAnalyzer):
        self.user = user
        self.token_usage_analyzer = token_usage_analyzer
        self.user_token_usage_analyzer = user_token_usage_analyzer

    @validate_permissions(permission=Permission.ADMIN)
    async def get_token_usage(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> TokenUsageSummary:
        """
        Get token usage statistics for the specified date range.
        If no dates are provided, returns data for the last 30 days.

        Args:
            start_date: The start date for the analysis period
            end_date: The end date for the analysis period

        Returns:
            A TokenUsageSummary object with aggregated token usage data
        """
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        return await self.token_usage_analyzer.get_model_token_usage(
            tenant_id=self.user.tenant_id, start_date=start_date, end_date=end_date
        )

    @validate_permissions(permission=Permission.ADMIN)
    async def get_user_token_usage(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> UserTokenUsageSummary:
        """
        Get token usage statistics aggregated by user for the specified date range.
        If no dates are provided, returns data for the last 30 days.

        Args:
            start_date: The start date for the analysis period
            end_date: The end date for the analysis period

        Returns:
            A UserTokenUsageSummary object with user-level token usage data
        """
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        return await self.user_token_usage_analyzer.get_user_token_usage(
            tenant_id=self.user.tenant_id, start_date=start_date, end_date=end_date
        )

    @validate_permissions(permission=Permission.ADMIN)
    async def get_user_model_breakdown(
        self, user_id: UUID, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> TokenUsageSummary:
        """
        Get model breakdown for a specific user within the specified date range.
        If no dates are provided, returns data for the last 30 days.

        Args:
            user_id: The user ID to get model breakdown for
            start_date: The start date for the analysis period
            end_date: The end date for the analysis period

        Returns:
            A TokenUsageSummary object with model breakdown for the user
        """
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        return await self.user_token_usage_analyzer.get_user_model_breakdown(
            tenant_id=self.user.tenant_id, user_id=user_id, start_date=start_date, end_date=end_date
        )
