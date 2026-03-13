from typing import Iterable, Any
from ruamel.yaml.comments import CommentedMap


class PushToAllBranches:
    id = "SUS002"
    description = "Workflows should be triggered only when necessary, not on all branches"

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        triggers = workflow.get("on")

        push: Any

        if triggers == "push":
            push = True
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
            yield Issue(
                rule_id=self.id,
                message="Workflow triggers on push to all branches. Add branch filters.",
                location="on.push",
            )



RULE: Rule = PushToAllBranches()