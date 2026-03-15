import xml.etree.ElementTree as ET
from xml.dom import minidom

from model import BPMNModel, BPMNElement, StartEvent, EndEvent, Task, ExclusiveGateway, SequenceFlow

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"

ET.register_namespace("bpmn", BPMN_NS)
ET.register_namespace("bpmndi", BPMNDI_NS)
ET.register_namespace("di", DI_NS)
ET.register_namespace("dc", DC_NS)

def _element_tag(element: BPMNElement) -> str:
    if isinstance(element, StartEvent): return "startEvent"
    if isinstance(element, EndEvent): return "endEvent"
    if isinstance(element, Task): return "task"
    if isinstance(element, ExclusiveGateway): return "exclusiveGateway"
    raise ValueError(f"Unknown element type {type(element)}")

def _create_element_node(element: BPMNElement) -> ET.Element:
    attrs = {"id": element.id, "name": element.name}
    return ET.Element(f"{{{BPMN_NS}}}{_element_tag(element)}", attrs)

def _create_sequence_flow_node(flow: SequenceFlow) -> ET.Element:
    attrs = {"id": flow.id, "sourceRef": flow.source_ref, "targetRef": flow.target_ref}
    if flow.condition:
        attrs["name"] = flow.condition 
    node = ET.Element(f"{{{BPMN_NS}}}sequenceFlow", attrs)
    if flow.condition:
        condition = ET.SubElement(node, f"{{{BPMN_NS}}}conditionExpression")
        condition.text = flow.condition
    return node

def _add_bpmndi(definitions: ET.Element, model: BPMNModel, process_id: str) -> None:
    diagram = ET.SubElement(definitions, f"{{{BPMNDI_NS}}}BPMNDiagram", {"id": "BPMNDiagram_1"})
    plane = ET.SubElement(diagram, f"{{{BPMNDI_NS}}}BPMNPlane", {"id": "BPMNPlane_1", "bpmnElement": process_id})

    # Hierarchical layout using BFS levels
    children = {e.id: [] for e in model.elements}
    for f in model.flows: children[f.source_ref].append(f.target_ref)

    start_ids = [e.id for e in model.elements if isinstance(e, StartEvent)]
    if not start_ids and model.elements: start_ids = [model.elements[0].id]

    level = {}
    from collections import deque
    dq = deque()
    for sid in start_ids:
        level[sid] = 0
        dq.append(sid)

    visited = set(start_ids)
    while dq:
        cur = dq.popleft()
        for nxt in children.get(cur, []):
            if nxt not in visited:
                level[nxt] = level[cur] + 1
                visited.add(nxt)
                dq.append(nxt)

    for e in model.elements:
        if e.id not in level:
            level[e.id] = max(level.values(), default=0) + 1

    from collections import defaultdict
    nodes_by_level = defaultdict(list)
    for nid, lvl in level.items():
        nodes_by_level[lvl].append(nid)

    for lvl in nodes_by_level:
        nodes_by_level[lvl].sort()

    element_positions = {}
    x_step = 150
    y_step = 80

    for lvl in sorted(nodes_by_level.keys()):
        x = 100 + lvl * x_step
        y_base = 100
        for i, nid in enumerate(nodes_by_level[lvl]):
            y = y_base + i * y_step
            element = next((e for e in model.elements if e.id == nid), None)
            w, h = 100, 80
            if isinstance(element, (StartEvent, EndEvent)):
                w, h = 36, 36
            elif isinstance(element, ExclusiveGateway):
                w, h = 50, 50

            element_positions[nid] = (x, y, w, h)
            
            shape = ET.SubElement(plane, f"{{{BPMNDI_NS}}}BPMNShape", {"id": f"BPMNShape_{nid}", "bpmnElement": nid})
            ET.SubElement(shape, f"{{{DC_NS}}}Bounds", {"x": str(x), "y": str(y), "width": str(w), "height": str(h)})

    # Orthogonal routing
    for flow in model.flows:
        edge = ET.SubElement(plane, f"{{{BPMNDI_NS}}}BPMNEdge", {"id": f"BPMNEdge_{flow.id}", "bpmnElement": flow.id})

        src_x, src_y, src_w, src_h = element_positions.get(flow.source_ref, (100, 100, 100, 80))
        tgt_x, tgt_y, tgt_w, tgt_h = element_positions.get(flow.target_ref, (200, 100, 100, 80))

        source_level = level.get(flow.source_ref, 0)
        target_level = level.get(flow.target_ref, 0)

        # connect from right side of source
        sx = src_x + src_w
        sy = src_y + src_h / 2

        # connect to left side of target
        tx = tgt_x
        ty = tgt_y + tgt_h / 2

        if target_level <= source_level:
            # Backward flow - route below the diagram
            sx_bottom = src_x + src_w / 2
            sy_bottom = src_y + src_h
            tx_bottom = tgt_x + tgt_w / 2
            ty_bottom = tgt_y + tgt_h
            
            lowest_y = max(sy_bottom, ty_bottom) + 40
            
            waypoints = [
                (sx_bottom, sy_bottom),
                (sx_bottom, lowest_y),
                (tx_bottom, lowest_y),
                (tx_bottom, ty_bottom)
            ]
        else:
            mid_x = (sx + tx) / 2
            
            waypoints = [
                (sx, sy),
                (mid_x, sy),
                (mid_x, ty),
                (tx, ty)
            ]

        for x, y in waypoints:
            ET.SubElement(edge, f"{{{DI_NS}}}waypoint", {"x": str(x), "y": str(y)})

def generate_bpmn_xml(model: BPMNModel, process_id="Process_1", process_name="Auto-generated process") -> str:
    definitions = ET.Element(f"{{{BPMN_NS}}}definitions", {"id": "Definitions_1", "targetNamespace": "http://example.com/bpmn"})
    process = ET.SubElement(definitions, f"{{{BPMN_NS}}}process", {"id": process_id, "name": process_name, "isExecutable": "false"})

    for element in model.elements: 
        process.append(_create_element_node(element))
    for flow in model.flows: 
        process.append(_create_sequence_flow_node(flow))

    _add_bpmndi(definitions, model, process_id)
    return minidom.parseString(ET.tostring(definitions, encoding="utf-8")).toprettyxml(indent="  ")
