"""Revision interval and state-transition algorithms."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Optional


REVIEW_STATES = ["NEW", "LEARNING", "REVIEW", "STRONG", "WEAK", "FORGOTTEN"]


class ReviewOutcome(str, Enum):
    CORRECT = "correct"
    PARTIAL = "partial"
    FORGOTTEN = "forgotten"


@dataclass(frozen=True)
class RevisionSchedule:
    state: str
    interval_days: int
    next_review_at: datetime
    last_reviewed_at: Optional[datetime]
    confidence: float
    recall_strength: float
    ease_factor: float
    review_count: int
    consecutive_correct: int
    algorithm: str


class RevisionAlgorithm:
    """Base revision algorithm contract."""

    def calculate_next(self, metadata: Dict[str, any], outcome: ReviewOutcome, confidence: float, now: Optional[datetime] = None) -> RevisionSchedule:
        raise NotImplementedError()

    def initial_schedule(self, metadata: Dict[str, any], now: Optional[datetime] = None) -> RevisionSchedule:
        raise NotImplementedError()


class SimpleRevisionAlgorithm(RevisionAlgorithm):
    """Simple deterministic interval scheduler."""

    BASE_INTERVAL_DAYS = 1
    MAX_INTERVAL_DAYS = 180

    DIFFICULTY_MULTIPLIER = {
        "low": 1.3,
        "medium": 1.0,
        "high": 0.8,
    }

    PRIORITY_MULTIPLIER = {
        "urgent": 1.4,
        "high": 1.2,
        "medium": 1.0,
        "low": 0.9,
    }

    STATE_MULTIPLIER = {
        "NEW": 1.0,
        "LEARNING": 1.2,
        "REVIEW": 1.5,
        "STRONG": 2.0,
        "WEAK": 0.9,
        "FORGOTTEN": 0.5,
    }

    DEFAULT_EASE = 2.5

    def initial_schedule(self, metadata: Dict[str, any], now: Optional[datetime] = None) -> RevisionSchedule:
        now = now or datetime.now(timezone.utc)
        return RevisionSchedule(
            state="NEW",
            interval_days=self.BASE_INTERVAL_DAYS,
            next_review_at=now + timedelta(days=self.BASE_INTERVAL_DAYS),
            last_reviewed_at=None,
            confidence=0.0,
            recall_strength=0.2,
            ease_factor=self.DEFAULT_EASE,
            review_count=0,
            consecutive_correct=0,
            algorithm="simple",
        )

    def calculate_next(self, metadata: Dict[str, any], outcome: ReviewOutcome, confidence: float, now: Optional[datetime] = None) -> RevisionSchedule:
        now = now or datetime.now(timezone.utc)
        previous = metadata or {}
        previous_state = previous.get("state", "NEW")
        previous_interval = max(int(previous.get("interval_days", self.BASE_INTERVAL_DAYS)), self.BASE_INTERVAL_DAYS)
        previous_strength = float(previous.get("recall_strength", 0.2))
        previous_ease = float(previous.get("ease_factor", self.DEFAULT_EASE))
        previous_consecutive = int(previous.get("consecutive_correct", 0))

        difficulty = str(previous.get("difficulty", "medium")).lower()
        priority = str(previous.get("recall_priority", "medium")).lower()

        difficulty_mult = self.DIFFICULTY_MULTIPLIER.get(difficulty, 1.0)
        priority_mult = self.PRIORITY_MULTIPLIER.get(priority, 1.0)
        state_mult = self.STATE_MULTIPLIER.get(previous_state, 1.0)
        confidence = max(0.0, min(1.0, confidence))

        if outcome == ReviewOutcome.CORRECT:
            next_interval = int(max(1, previous_interval * (1.8 + confidence * 0.4) * difficulty_mult * priority_mult * state_mult))
            next_state = "STRONG" if confidence >= 0.8 and previous_consecutive >= 1 else "REVIEW"
            recall_strength = min(1.0, previous_strength + 0.15 + (confidence - 0.5) * 0.2)
            consecutive_correct = previous_consecutive + 1
        elif outcome == ReviewOutcome.PARTIAL:
            next_interval = int(max(1, previous_interval * (1.1 + confidence * 0.2) * difficulty_mult * priority_mult * state_mult))
            next_state = "LEARNING" if previous_state in {"NEW", "LEARNING", "WEAK", "FORGOTTEN"} else "REVIEW"
            recall_strength = max(0.1, previous_strength - 0.05 + confidence * 0.1)
            consecutive_correct = 0
        else:
            next_interval = self.BASE_INTERVAL_DAYS
            next_state = "FORGOTTEN"
            recall_strength = max(0.05, previous_strength * 0.6)
            consecutive_correct = 0

        ease_factor = max(1.3, previous_ease + (confidence - 0.6) * 0.1)
        next_review_at = now + timedelta(days=next_interval)

        return RevisionSchedule(
            state=next_state,
            interval_days=min(next_interval, self.MAX_INTERVAL_DAYS),
            next_review_at=next_review_at,
            last_reviewed_at=now,
            confidence=confidence,
            recall_strength=round(recall_strength, 3),
            ease_factor=round(ease_factor, 3),
            review_count=int(previous.get("review_count", 0)) + 1,
            consecutive_correct=consecutive_correct,
            algorithm="simple",
        )


class AdaptiveRevisionAlgorithm(SimpleRevisionAlgorithm):
    """Adaptive algorithm designed for future FSRS compatibility."""

    def calculate_next(self, metadata: Dict[str, any], outcome: ReviewOutcome, confidence: float, now: Optional[datetime] = None) -> RevisionSchedule:
        schedule = super().calculate_next(metadata, outcome, confidence, now=now)
        if outcome == ReviewOutcome.CORRECT and schedule.state == "STRONG":
            schedule = schedule.__class__(
                state=schedule.state,
                interval_days=min(schedule.interval_days + 1, self.MAX_INTERVAL_DAYS),
                next_review_at=schedule.next_review_at + timedelta(days=1),
                last_reviewed_at=schedule.last_reviewed_at,
                confidence=schedule.confidence,
                recall_strength=schedule.recall_strength,
                ease_factor=schedule.ease_factor,
                review_count=schedule.review_count,
                consecutive_correct=schedule.consecutive_correct,
                algorithm="adaptive",
            )
        return schedule
