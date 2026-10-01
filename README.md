# trade-doc-fixtures

Synthetic gold documents for the shipment DocFlow is meant to read, plus a scorer that says whether an extraction actually got the fields.

[DocFlow Extractor](https://github.com/whistlenrye/docflow-extractor) ships one commercial-invoice sample. Clearance needs the set: invoice, packing list, bill of lading, and certificate of origin, all for the **same** fictional shipment (`INV-2026-1187`). These four texts use the same labels the DocFlow parser already looks for (`Shipper / Exporter`, `Invoice Number`, pipe tables).

No real company, no personal data, no chamber stamp.

## Layout

```text
fixtures/
  catalog.json
  commercial_invoice/document.txt + expected.json
  packing_list/document.txt + expected.json
  bill_of_lading/document.txt + expected.json
  certificate_of_origin/document.txt + expected.json
```

`expected.json` is a DocFlow `ExtractionResult` plus an optional `transport` object (bill numbers, vessel, ports, weights, container). The extractor does not emit `transport` yet. That gap is the point of the score: a perfect copy of today's parser output will miss `transport.ocean_bill` and should.

## Score an extraction

```bash
python3 -m trade_doc_fixtures path/to/actual.json fixtures/packing_list/expected.json
```

The report is gold-field recall. Only fields that are set on the gold file count. Extra keys on the actual file are ignored. Numbers match within two cents or 0.1%. Text is lower-cased with punctuation collapsed.

Exit `0` when recall is at least `--threshold` (default `1.0`).

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## How this fits

```text
trade-doc-fixtures    this repo — the measuring stick
docflow-extractor     the reader
shipment-crosscheck   do invoice, packing list, and bill agree?
ics-n10-worksheet     N10 review sheet, not an ICS lodgement
```

Drop `document.txt` into DocFlow as a pasted sample or a `.txt` upload. Score the JSON it returns against `expected.json`. Do not treat a high score as permission to file a declaration.

## License

MIT.
