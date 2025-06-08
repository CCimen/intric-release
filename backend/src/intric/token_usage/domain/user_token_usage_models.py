from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from intric.token_usage.domain.token_usage_models import ModelTokenUsage


@dataclass
class UserTokenUsage:
    """Token usage data for a specific user."""
    user_id: UUID
    username: str
    email: str
    total_input_tokens: int
    total_output_tokens: int
    total_requests: int
    models_used: list[ModelTokenUsage]

    @property
    def total_tokens(self) -> int:
        """Get total token usage (input + output)."""
        return self.total_input_tokens + self.total_output_tokens


@dataclass
class UserTokenUsageSummary:
    """Summary of token usage across multiple users."""
    users: list[UserTokenUsage]
    start_date: datetime
    end_date: datetime

    @property
    def total_users(self) -> int:
        """Get total number of users with token usage."""
        return len(self.users)

    @property
    def total_input_tokens(self) -> int:
        """Get total input tokens across all users."""
        return sum(user.total_input_tokens for user in self.users)

    @property
    def total_output_tokens(self) -> int:
        """Get total output tokens across all users."""
        return sum(user.total_output_tokens for user in self.users)

    @property
    def total_tokens(self) -> int:
        """Get total tokens across all users."""
        return self.total_input_tokens + self.total_output_tokens

    @property
    def total_requests(self) -> int:
        """Get total requests across all users."""
        return sum(user.total_requests for user in self.users)