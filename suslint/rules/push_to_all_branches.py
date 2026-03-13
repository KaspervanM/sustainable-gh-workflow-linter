from typing import Iterable
from suslint.rule import Issue, Rule


def get_workflow_triggers(workflow: dict[str, object]) -> dict[str, object]:
    """
    For some reason pyYaml replaces "on" with True.
    """
    return workflow.get("on", workflow.get(True, {}))


class PushToAllBranches:
    id = "SUS002"
    description = "Workflows should be triggered only when necessary, not on all branches"

    def check(self, workflow: dict[str, object]) -> Iterable[Issue]:
        triggers = get_workflow_triggers(workflow)

        if triggers == "push":
            push = True
        elif not isinstance(triggers, dict):
            return
        else:
            push = triggers.get("push")
        
        if push is None:
            if "push" in triggers.keys():
                push = True
            else:
                return
        
        # It triggers on all branches if push is true or no branch filters specified
        if push is True or (
            isinstance(push, dict)
            and not push.get("branches")
            and not push.get("branches-ignore")
        ):
            yield Issue(
                rule_id=self.id,
                message="Workflow triggers on push to all branches. Add branch filters.",
                location="on.push",
            )



RULE: Rule = PushToAllBranches()