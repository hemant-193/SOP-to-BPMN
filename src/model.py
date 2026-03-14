from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BPMNElement:
    id: str
    name: str
    label: str = None

@dataclass
class StartEvent(BPMNElement):
    pass

@dataclass
class EndEvent(BPMNElement):
    pass

@dataclass
class Task(BPMNElement):
    pass

@dataclass
class ExclusiveGateway(BPMNElement):
    pass

# Sequence flow connecting the elements
@dataclass
class SequenceFlow:
    id: str
    source_ref: str  # The ID of the element where the arrow starts
    target_ref: str  # The ID of the element where the arrow points
    condition: Optional[str] = None  # E.g., "Yes" or "No" for branches
    is_jump: bool = False

# A container to hold the entire parsed model
@dataclass
class BPMNModel:
    elements: list[BPMNElement] = field(default_factory=list)
    flows: list[SequenceFlow] = field(default_factory=list)
    
    def add_element(self, element: BPMNElement):
        self.elements.append(element)
        
    def add_flow(self, flow: SequenceFlow):
        self.flows.append(flow)