import argparse
import os

from parser import DocxSOPParser
from mapper import SOPToBPMNMapper
from generator import generate_bpmn_xml


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert SOP documents to BPMN XML")
    parser.add_argument("input", help="Input SOP .docx file")
    parser.add_argument("output", help="Output BPMN .bpmn file")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return

    try:
        # Parse the document
        sop_parser = DocxSOPParser()
        raw_steps = sop_parser.parse(args.input)
        print(f"Parsed {len(raw_steps)} steps from {args.input}")

        # Map to BPMN model
        mapper = SOPToBPMNMapper()
        model = mapper.map_steps(raw_steps)
        print(f"Generated BPMN model with {len(model.elements)} elements and {len(model.flows)} flows")

        # Generate XML
        xml = generate_bpmn_xml(model)

        # Write output
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(xml)

        print(f"Successfully wrote {args.output}")

    except Exception as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":
    main()
