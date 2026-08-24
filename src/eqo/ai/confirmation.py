from eqo.ai.models import InterpretationDisposition, InterpretationOutcome


class ConfirmationGate:
    def resolve(
        self, outcome: InterpretationOutcome, confirmed: bool
    ) -> InterpretationOutcome:
        if outcome.disposition is not InterpretationDisposition.CONFIRM:
            return outcome
        disposition = (
            InterpretationDisposition.ACCEPT
            if confirmed
            else InterpretationDisposition.UNKNOWN
        )
        return InterpretationOutcome(disposition, outcome.interpretation)

