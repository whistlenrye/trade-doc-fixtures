# Decisions

## One shipment, four documents
Scoring a single invoice cannot tell you whether the packing list and the bill describe the same cargo. All four fixtures share invoice `INV-2026-1187`.

## Gold files include `transport`
DocFlow's schema does not have bill numbers, vessel, ports, or weights yet. Putting them only in prose would make the miss invisible. The scorer fails those paths until the extractor grows the fields.

## Recall, not a model benchmark
The score counts gold fields that came back. It does not call Gemini and it does not rank models.
