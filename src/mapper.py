import re
from typing import List, Dict, Set
from model import BPMNModel, StartEvent, EndEvent, Task, ExclusiveGateway, SequenceFlow

class SOPToBPMNMapper:
    def __init__(self):
        self.id_counter = 1

    def _next_id(self, prefix: str) -> str:
        _id = f"{prefix}_{self.id_counter}"
        self.id_counter += 1
        return _id

    def map_steps(self, steps: List[str]) -> BPMNModel:
        model = BPMNModel()
        start = StartEvent(id="StartEvent_1", name="Start")
        model.add_element(start)

        # Keep track of which step labels map to which BPMN element IDs
        registry: Dict[str, str] = {}
        # Store gateway IDs for decision points
        gateways: Dict[str, str] = {}
        # Current active endpoints where we can add new elements
        active_leaves: Set[str] = {start.id}
        # Jumps that need to be resolved later
        pending_jumps = []

        # Remember the last decision point for flat branching
        last_decision_label = None

        def clean_condition(c: str) -> str:
            c = c.strip(" ,.")
            if c.lower().startswith("if "):
                return c[3:].strip(" ,.")
            return c

        def add_flow(src: str, tgt: str, cond: str = None):
            model.add_flow(SequenceFlow(id=self._next_id("Flow"), source_ref=src, target_ref=tgt, condition=cond))
            if src in active_leaves:
                active_leaves.remove(src)
            active_leaves.add(tgt)

        # Parse the raw steps into labeled ones
        parsed_steps = []
        for step in steps:
            match = re.match(r"^\s*(\d+(?:\.\d+)*)[\.)]?\s*(.*)$", step)
            if match:
                label, text = match.groups()
                parsed_steps.append({"label": label, "text": text.strip()})
            elif step.strip():
                parsed_steps.append({"label": None, "text": step.strip()})

        for step_data in parsed_steps:
            label = step_data["label"]
            text = step_data["text"]
            lower_text = text.lower()

            # Mark this as a decision if it looks like a question
            if "check if" in lower_text or "?" in lower_text:
                last_decision_label = label

            jump_match = re.search(r"(?:go back to|return to|go to)\s*(?:step\s*)?([\d\.]+)", lower_text)
            is_conditional = lower_text.startswith("if ")
            condition = None
            action = text

            if is_conditional:
                if "," in text and not jump_match:
                    parts = text.split(",", 1)
                    condition = clean_condition(parts[0])
                    action = parts[1].strip(" ,.")
                elif jump_match:
                    condition = clean_condition(text.replace(jump_match.group(0), ""))
                    action = "JUMP"
                else:
                    condition = clean_condition(text)
                    action = "Evaluate"

            source_ids = []

            # Figure out where this step connects from
            is_flat_branch = is_conditional and (lower_text.startswith("if yes") or lower_text.startswith("if no"))

            if is_flat_branch and last_decision_label:
                parent_label = last_decision_label
            else:
                parent_label = label.rsplit(".", 1)[0] if label and "." in label else None

            if parent_label and parent_label in registry:
                if parent_label not in gateways:
                    gw_id = self._next_id("ExclusiveGateway")

                    parent_text = "Decision"
                    for p in parsed_steps:
                        if p["label"] == parent_label:
                            parent_text = p["text"]
                            break

                    model.add_element(ExclusiveGateway(id=gw_id, name=f"{parent_text}?"))
                    add_flow(registry[parent_label], gw_id)
                    gateways[parent_label] = gw_id
                source_ids = [gateways[parent_label]]
            else:
                source_ids = list(active_leaves)

            if action == "JUMP":
                target_label = jump_match.group(1).rstrip('.')
                for src in source_ids:
                    pending_jumps.append((src, condition, target_label))
                    if src in active_leaves:
                        active_leaves.remove(src)
            else:
                task_id = self._next_id("Task")
                model.add_element(Task(id=task_id, name=action))
                if label:
                    registry[label] = task_id

                for src in source_ids:
                    add_flow(src, task_id, condition)

        end = EndEvent(id="EndEvent_1", name="End")
        model.add_element(end)

        # Connect all remaining active leaves to the end
        for leaf in list(active_leaves):
            add_flow(leaf, end.id)

        # Now resolve any pending jumps
        for src, cond, tgt_label in pending_jumps:
            if tgt_label in registry:
                add_flow(src, registry[tgt_label], cond)

        return model
    