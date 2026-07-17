from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ScoringWeights:
    """Centralized scoring weights for lead quality factors."""

    destination_selected: int = 15
    travel_month_available: int = 15
    travellers_known: int = 10
    budget_available: int = 15
    budget_realistic: int = 10
    customer_intent: int = 15
    trip_type: int = 10
    additional_requirements: int = 10


@dataclass(frozen=True)
class LeadScoreResult:
    """Business intelligence output for a travel lead."""

    lead_score: int
    lead_priority: str
    lead_reason: str
    booking_intent: str
    travel_urgency: str
    next_action: str
    follow_up_action: str
    lead_summary: str


class LeadScoringService:
    """Evaluate lead quality and recommend consultant action."""

    HIGH_INTENT_WORDS = (
        "book",
        "booking",
        "confirmed",
        "ready",
        "finalize",
        "payment",
        "qualified",
        "urgent",
    )
    MEDIUM_INTENT_WORDS = (
        "interested",
        "planning",
        "package",
        "quote",
        "itinerary",
        "options",
    )
    PREMIUM_TRIP_TYPES = ("honeymoon", "family", "anniversary", "luxury")
    EUROPE_DESTINATIONS = ("europe", "paris", "switzerland", "italy", "france", "spain", "greece")
    MONTHS = {
        "january": 1,
        "jan": 1,
        "february": 2,
        "feb": 2,
        "march": 3,
        "mar": 3,
        "april": 4,
        "apr": 4,
        "may": 5,
        "june": 6,
        "jun": 6,
        "july": 7,
        "jul": 7,
        "august": 8,
        "aug": 8,
        "september": 9,
        "sep": 9,
        "october": 10,
        "oct": 10,
        "november": 11,
        "nov": 11,
        "december": 12,
        "dec": 12,
    }

    def __init__(self, settings: Settings, weights: ScoringWeights | None = None) -> None:
        self.settings = settings
        self.weights = weights or ScoringWeights(
            destination_selected=settings.lead_score_weight_destination,
            travel_month_available=settings.lead_score_weight_travel_month,
            travellers_known=settings.lead_score_weight_travellers,
            budget_available=settings.lead_score_weight_budget_available,
            budget_realistic=settings.lead_score_weight_budget_realistic,
            customer_intent=settings.lead_score_weight_customer_intent,
            trip_type=settings.lead_score_weight_trip_type,
            additional_requirements=settings.lead_score_weight_additional_requirements,
        )

    def score(self, lead_values: dict[str, Any]) -> LeadScoreResult:
        """Return scoring, priority, intent, urgency, and next action for a lead."""

        score = 0
        reasons: list[str] = []

        score += self._score_presence(
            lead_values.get("destination"),
            self.weights.destination_selected,
            "Destination selected",
            "Destination missing",
            reasons,
        )
        score += self._score_presence(
            lead_values.get("travel_month"),
            self.weights.travel_month_available,
            "Travel month available",
            "Travel month missing",
            reasons,
        )
        score += self._score_presence(
            lead_values.get("travellers"),
            self.weights.travellers_known,
            "Traveller count known",
            "Traveller count missing",
            reasons,
        )
        score += self._score_presence(
            lead_values.get("budget"),
            self.weights.budget_available,
            "Budget available",
            "Budget missing",
            reasons,
        )
        score += self._score_realistic_budget(lead_values, reasons)
        score += self._score_customer_intent(lead_values, reasons)
        score += self._score_trip_type(lead_values, reasons)
        score += self._score_presence(
            lead_values.get("additional_requirements"),
            self.weights.additional_requirements,
            "Specific requirements shared",
            "No additional requirements shared",
            reasons,
        )

        bounded_score = max(0, min(100, score))
        priority = self._priority_for_score(bounded_score)
        intent = self._intent_for_score(bounded_score)
        urgency = self._travel_urgency(lead_values.get("travel_month"))
        action = self._next_action(lead_values, priority, urgency)
        summary = self._summary(lead_values, intent)
        reason = "; ".join(reasons)

        logger.info("Score calculated score=%s", bounded_score)
        logger.info("Priority assigned priority=%s", priority)
        logger.info("Reason generated reason=%s", reason)
        logger.info("Next action generated action=%s", action)
        self._log_business_rule_gaps(lead_values)

        return LeadScoreResult(
            lead_score=bounded_score,
            lead_priority=priority,
            lead_reason=reason,
            booking_intent=intent,
            travel_urgency=urgency,
            next_action=action,
            follow_up_action=action,
            lead_summary=summary,
        )

    def _score_presence(
        self,
        value: Any,
        weight: int,
        positive_reason: str,
        negative_reason: str,
        reasons: list[str],
    ) -> int:
        """Score a factor when the lead supplied a useful value."""

        if value is None or value == "":
            reasons.append(f"{negative_reason} (+0)")
            return 0
        reasons.append(f"{positive_reason} (+{weight})")
        return weight

    def _score_realistic_budget(self, lead_values: dict[str, Any], reasons: list[str]) -> int:
        """Score whether the budget is high enough to be commercially actionable."""

        budget = lead_values.get("budget")
        if not isinstance(budget, Decimal):
            reasons.append("Budget realism unknown (+0)")
            return 0

        if budget >= Decimal(self.settings.lead_realistic_budget_min):
            reasons.append(f"Budget appears realistic (+{self.weights.budget_realistic})")
            return self.weights.budget_realistic

        reasons.append("Budget may be low for packaged travel (+0)")
        return 0

    def _score_customer_intent(self, lead_values: dict[str, Any], reasons: list[str]) -> int:
        """Score conversion intent from outcome and free-text requirements."""

        signal_text = " ".join(
            str(value or "")
            for value in (
                lead_values.get("outcome"),
                lead_values.get("additional_requirements"),
                lead_values.get("trip_type"),
            )
        ).lower()

        if any(word in signal_text for word in self.HIGH_INTENT_WORDS):
            reasons.append(f"Strong buying intent detected (+{self.weights.customer_intent})")
            return self.weights.customer_intent

        if any(word in signal_text for word in self.MEDIUM_INTENT_WORDS):
            partial_score = round(self.weights.customer_intent * 0.6)
            reasons.append(f"Moderate planning intent detected (+{partial_score})")
            return partial_score

        reasons.append("No clear buying intent detected (+0)")
        return 0

    def _score_trip_type(self, lead_values: dict[str, Any], reasons: list[str]) -> int:
        """Score whether the caller shared the purpose of travel."""

        trip_type = lead_values.get("trip_type")
        if not trip_type:
            reasons.append("Trip type missing (+0)")
            return 0

        normalized_trip_type = str(trip_type).lower()
        if any(value in normalized_trip_type for value in self.PREMIUM_TRIP_TYPES):
            reasons.append(f"High-context trip type known (+{self.weights.trip_type})")
            return self.weights.trip_type

        reasons.append(f"Trip type known (+{self.weights.trip_type})")
        return self.weights.trip_type

    def _priority_for_score(self, score: int) -> str:
        """Convert numeric score into transparent lead priority."""

        if score >= self.settings.lead_hot_threshold:
            return "HOT"
        if score >= self.settings.lead_warm_threshold:
            return "WARM"
        return "COLD"

    def _intent_for_score(self, score: int) -> str:
        """Classify booking intent using configurable score thresholds."""

        if score >= self.settings.lead_high_intent_threshold:
            return "HIGH"
        if score >= self.settings.lead_medium_intent_threshold:
            return "MEDIUM"
        return "LOW"

    def _travel_urgency(self, travel_month: Any) -> str:
        """Classify urgency from the captured travel month."""

        if not travel_month:
            return "Unknown"

        normalized = str(travel_month).strip().lower()
        if any(keyword in normalized for keyword in ("now", "urgent", "asap", "this month")):
            return "Immediate"

        month_number = self._extract_month_number(normalized)
        if month_number is None:
            if any(keyword in normalized for keyword in ("next year", "future", "later")):
                return "Future Planning"
            return "Unknown"

        now = datetime.now()
        months_until_trip = (month_number - now.month) % 12
        if months_until_trip == 0:
            return "Immediate"
        if months_until_trip <= 3:
            return "Within 3 Months"
        if months_until_trip <= 11:
            return "3-12 Months"
        return "Future Planning"

    def _extract_month_number(self, value: str) -> int | None:
        """Extract a calendar month from natural text."""

        for month_name, month_number in self.MONTHS.items():
            if month_name in value:
                return month_number
        return None

    def _next_action(self, lead_values: dict[str, Any], priority: str, urgency: str) -> str:
        """Recommend the next practical consultant action."""

        destination = str(lead_values.get("destination") or "").lower()
        trip_type = str(lead_values.get("trip_type") or "").lower()

        if lead_values.get("budget") is None:
            return "Collect missing budget information"
        if priority == "HOT" and urgency in {"Immediate", "Within 3 Months"}:
            return "Call within 2 hours"
        if "honeymoon" in trip_type:
            return "Send honeymoon package"
        if any(place in destination for place in self.EUROPE_DESTINATIONS):
            return "Share Europe itinerary"
        if priority == "WARM":
            return "Schedule follow-up next week"
        return "Nurture with destination options"

    def _summary(self, lead_values: dict[str, Any], intent: str) -> str:
        """Generate a short professional lead summary."""

        travellers = lead_values.get("travellers")
        destination = lead_values.get("destination") or "an undecided destination"
        travel_month = lead_values.get("travel_month") or "an undecided travel month"
        budget = lead_values.get("budget")
        trip_type = lead_values.get("trip_type")

        traveller_phrase = f"{travellers} traveller(s)" if travellers else "Traveller count unknown"
        trip_phrase = f"{trip_type} trip" if trip_type else "trip"
        budget_phrase = f" with a budget of {budget:.2f}" if isinstance(budget, Decimal) else " with budget pending"

        return (
            f"{traveller_phrase} planning a {trip_phrase} to {destination} in {travel_month}"
            f"{budget_phrase}. Booking intent is {intent.lower()}."
        )

    def _log_business_rule_gaps(self, lead_values: dict[str, Any]) -> None:
        """Log missing inputs that limit scoring confidence."""

        missing_fields = [
            field_name
            for field_name in ("destination", "travel_month", "travellers", "budget", "trip_type")
            if not lead_values.get(field_name)
        ]
        if missing_fields:
            logger.warning("Business rule gaps detected missing_fields=%s", ",".join(missing_fields))
