"""Local matching between contacts and race results."""

from .models import MatchReport, MatchResult
from .service import match_dataset

__all__ = ["MatchReport", "MatchResult", "match_dataset"]
