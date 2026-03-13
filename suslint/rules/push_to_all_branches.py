from typing import Iterable, Any
from ruamel.yaml.comments import CommentedMap
from suslint.rule import Location, Issue, Rule
from suslint.position import pos


class PushToAllBranches:
    id = "SUS002"
    description = "Workflows should be triggered only when necessary, not on all branches"

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        triggers = workflow.get("on")
        location = None

        push: Any

        if triggers == "push":
            push = True
            location = Location("on", *pos(workflow, "on"))
        elif not isinstance(triggers, CommentedMap):
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
            isinstance(push, CommentedMap)
            and not push.get("branches")
            and not push.get("branches-ignore")
        ):
            if not location:
                location = Location("on.push", *pos(triggers, "push"))
            yield Issue(
                rule_id=self.id,
                message="Workflow triggers on push to all branches. Add branch filters.",
                location=location,
            )



RULE: Rule = PushToAllBranches()