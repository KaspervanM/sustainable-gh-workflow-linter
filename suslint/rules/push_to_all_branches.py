from typing import Any, Iterable

from ruamel.yaml.comments import CommentedMap

from suslint.position import pos
from suslint.rule import Issue, Location, Rule, RuleMetadata
from suslint.workflow import get_event_trigger, has_branch_filters


class PushToAllBranches:
    id = "SUS002"
    description = "Workflows should be triggered only when necessary, not on all branches"
    metadata = RuleMetadata(
        severity="warning",
        category="trigger-scope",
        remediation="Restrict push triggers with branches or branches-ignore filters.",
    )

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        triggers = workflow.get("on")
        location = None

        push: Any = get_event_trigger(workflow, "push")

        if triggers == "push":
            push = True
            location = Location("on", *pos(workflow, "on"))
        elif not isinstance(triggers, CommentedMap):
            return

        if push is None:
            return

        # It triggers on all branches if push is true or no branch filters specified
        if push is True or not has_branch_filters(push):
            if not location:
                location = Location("on.push", *pos(triggers, "push"))
            yield Issue(
                rule_id=self.id,
                message="Workflow triggers on push to all branches. Add branch filters.",
                location=location,
            )



RULE: Rule = PushToAllBranches()
