from typing import TYPE_CHECKING

from sqlalchemy import func, select, union_all

from intric.database.tables.ai_models_table import CompletionModels
from intric.database.tables.app_table import AppRuns
from intric.database.tables.questions_table import Questions
from intric.database.tables.sessions_table import Sessions
from intric.database.tables.users_table import Users
from intric.token_usage.domain.token_usage_models import (
    ModelTokenUsage,
    TokenUsageSummary,
)
from intric.token_usage.domain.user_token_usage_models import (
    UserTokenUsage,
    UserTokenUsageSummary,
)

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class UserTokenUsageAnalyzer:
    """
    Analyzer for user-level token usage statistics.
    This class handles querying and aggregating token usage data by user without
    using a traditional repository.
    """

    def __init__(self, session: "AsyncSession"):
        self.session = session

    async def get_user_token_usage(
        self, tenant_id: "UUID", start_date: "datetime", end_date: "datetime"
    ) -> UserTokenUsageSummary:
        """
        Get token usage statistics aggregated by user.

        Args:
            tenant_id: The tenant ID to filter by
            start_date: The start date for the analysis period
            end_date: The end date for the analysis period

        Returns:
            A UserTokenUsageSummary with token usage per user
        """

        # Simplified query - get token usage from both questions and app_runs in one query
        final_query = select(
            Users.id.label("user_id"),
            Users.username.label("username"),
            Users.email.label("email"),
            (
                func.coalesce(func.sum(Questions.num_tokens_question), 0) +
                func.coalesce(func.sum(AppRuns.num_tokens_input), 0)
            ).label("input_tokens"),
            (
                func.coalesce(func.sum(Questions.num_tokens_answer), 0) +
                func.coalesce(func.sum(AppRuns.num_tokens_output), 0)
            ).label("output_tokens"),
            (
                func.coalesce(func.count(Questions.id), 0) +
                func.coalesce(func.count(AppRuns.id), 0)
            ).label("request_count"),
        ).select_from(
            Users.__table__
            .outerjoin(Sessions.__table__, Sessions.user_id == Users.id)
            .outerjoin(Questions.__table__, 
                (Questions.session_id == Sessions.id) &
                (Questions.tenant_id == tenant_id) &
                (Questions.created_at >= start_date) &
                (Questions.created_at <= end_date)
            )
            .outerjoin(AppRuns.__table__,
                (AppRuns.user_id == Users.id) &
                (AppRuns.tenant_id == tenant_id) &
                (AppRuns.created_at >= start_date) &
                (AppRuns.created_at <= end_date)
            )
        ).where(
            Users.tenant_id == tenant_id
        ).group_by(
            Users.id, Users.username, Users.email
        ).having(
            # Only include users with actual token usage
            (func.coalesce(func.sum(Questions.num_tokens_question), 0) +
             func.coalesce(func.sum(Questions.num_tokens_answer), 0) +
             func.coalesce(func.sum(AppRuns.num_tokens_input), 0) +
             func.coalesce(func.sum(AppRuns.num_tokens_output), 0)) > 0
        )

        # Execute the query
        result = await self.session.execute(final_query)
        rows = result.all()

        # Transform the result into UserTokenUsage objects
        user_token_usages = []
        for row in rows:
            if row.user_id is not None:
                user_token_usages.append(
                    UserTokenUsage(
                        user_id=row.user_id,
                        username=row.username,
                        email=row.email,
                        total_input_tokens=row.input_tokens or 0,
                        total_output_tokens=row.output_tokens or 0,
                        total_requests=row.request_count or 0,
                        models_used=[],  # Load only when needed for detail view
                    )
                )

        return UserTokenUsageSummary(
            users=user_token_usages,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_user_model_breakdown(
        self, tenant_id: "UUID", user_id: "UUID", start_date: "datetime", end_date: "datetime"
    ) -> TokenUsageSummary:
        """
        Get model breakdown for a specific user.

        Args:
            tenant_id: The tenant ID to filter by
            user_id: The user ID to get breakdown for
            start_date: The start date for the analysis period
            end_date: The end date for the analysis period

        Returns:
            A TokenUsageSummary with model breakdown for the user
        """
        return await self._get_user_model_breakdown(tenant_id, user_id, start_date, end_date)

    async def _get_user_model_breakdown(
        self, tenant_id: "UUID", user_id: "UUID", start_date: "datetime", end_date: "datetime"
    ) -> TokenUsageSummary:
        """
        Internal method to get model breakdown for a specific user.
        This reuses the existing TokenUsageAnalyzer pattern but filters by user_id.
        """
        
        # Get token usage from questions (chat messages) for this user - join through sessions
        questions_query = (
            select(
                Questions.completion_model_id.label("model_id"),
                CompletionModels.name.label("model_name"),
                CompletionModels.nickname.label("model_nickname"),
                CompletionModels.org.label("model_org"),
                func.sum(Questions.num_tokens_question).label("input_tokens"),
                func.sum(Questions.num_tokens_answer).label("output_tokens"),
                func.count(Questions.id).label("request_count"),
            )
            .join(Sessions, Questions.session_id == Sessions.id)
            .join(
                CompletionModels,
                Questions.completion_model_id == CompletionModels.id,
            )
            .where(Questions.tenant_id == tenant_id)
            .where(Sessions.user_id == user_id)
            .where(Questions.created_at >= start_date)
            .where(Questions.created_at <= end_date)
            .group_by(
                Questions.completion_model_id,
                CompletionModels.name,
                CompletionModels.nickname,
                CompletionModels.org,
            )
        )

        # Get token usage from app runs for this user
        app_runs_query = (
            select(
                AppRuns.completion_model_id.label("model_id"),
                CompletionModels.name.label("model_name"),
                CompletionModels.nickname.label("model_nickname"),
                CompletionModels.org.label("model_org"),
                func.sum(func.coalesce(AppRuns.num_tokens_input, 0)).label(
                    "input_tokens"
                ),
                func.sum(func.coalesce(AppRuns.num_tokens_output, 0)).label(
                    "output_tokens"
                ),
                func.count(AppRuns.id).label("request_count"),
            )
            .join(
                CompletionModels,
                AppRuns.completion_model_id == CompletionModels.id,
            )
            .where(AppRuns.tenant_id == tenant_id)
            .where(AppRuns.user_id == user_id)
            .where(AppRuns.created_at >= start_date)
            .where(AppRuns.created_at <= end_date)
            .group_by(
                AppRuns.completion_model_id,
                CompletionModels.name,
                CompletionModels.nickname,
                CompletionModels.org,
            )
        )

        # Combine the results from both queries using union_all
        combined_usage_query = union_all(questions_query, app_runs_query).alias(
            "combined_usage"
        )

        # Sum up the input/output tokens and request counts for each model
        final_query = select(
            combined_usage_query.c.model_id,
            combined_usage_query.c.model_name,
            combined_usage_query.c.model_nickname,
            combined_usage_query.c.model_org,
            func.sum(combined_usage_query.c.input_tokens).label("input_tokens"),
            func.sum(combined_usage_query.c.output_tokens).label("output_tokens"),
            func.sum(combined_usage_query.c.request_count).label("request_count"),
        ).group_by(
            combined_usage_query.c.model_id,
            combined_usage_query.c.model_name,
            combined_usage_query.c.model_nickname,
            combined_usage_query.c.model_org,
        )

        # Execute the query
        result = await self.session.execute(final_query)
        rows = result.all()

        # Transform the result into ModelTokenUsage objects
        token_usage_by_model = []
        for row in rows:
            if row.model_id is not None:
                token_usage_by_model.append(
                    ModelTokenUsage(
                        model_id=row.model_id,
                        model_name=row.model_name,
                        model_nickname=row.model_nickname,
                        model_org=row.model_org,
                        input_token_usage=row.input_tokens or 0,
                        output_token_usage=row.output_tokens or 0,
                        request_count=row.request_count or 0,
                    )
                )

        return TokenUsageSummary.from_model_usages(
            model_usages=token_usage_by_model, start_date=start_date, end_date=end_date
        )