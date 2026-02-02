"""Import-safe Data Flow Mapper."""
from __future__ import annotations
class DataFlowMapper:
    def generate_mermaid_diagram(self, flows):
        lines = ["flowchart LR"]
        for f in flows or []:
            src = str(f.get("source","A")).replace(" ","_")
            dst = str(f.get("destination","B")).replace(" ","_")
            lines.append(f"{src} --> {dst}")
        return "\n".join(lines)
