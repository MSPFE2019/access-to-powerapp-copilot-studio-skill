# Access → Dataverse Data Type Mapping (for Power Apps Code Apps)

| Access Type | Dataverse Column Type | Notes |
|---|---|---|
| AutoNumber | Autonumber | Dataverse has a native Autonumber column; do not recreate manually. |
| Short Text | Text | Match max length where possible. |
| Long Text (Memo) | Multiline Text | Enable rich text if the Access memo field used rich text. |
| Number (Integer/Long/Byte) | Whole Number | Match precision/range. |
| Number (Single/Double) | Decimal Number / Floating Point Number | Use Decimal for money-adjacent precision needs. |
| Currency | Currency | Set correct currency/locale for the environment. |
| Date/Time | Date and Time | Watch timezone handling differences (Dataverse stores UTC). |
| Yes/No | Two Options | Set matching display labels. |
| OLE Object | File or Image column | Dataverse file/image columns are per-column, more granular than Access OLE. |
| Hyperlink | URL (Text with format) | |
| Lookup Field (single value) | Lookup (relationship) | Create the real Dataverse relationship, don't flatten to text. |
| Lookup Field (multi-value) | N:N relationship | |
| Attachment | File column(s) | |
| Calculated Field | Calculated or Rollup column | Prefer server-side Dataverse calculated/rollup columns over client (TypeScript) computed values when the value must be queryable/reportable. |
| Big Number (Access 2019+) | Decimal Number | Dataverse has no native 128-bit big integer; use Decimal if range requires it. |
| GUID | Unique Identifier | |

## Relationship / constraint notes

- Access enforced referential integrity + cascade update/delete → configure
  Dataverse relationship behavior (Referential / Parental / Cascade)
  explicitly per relationship; do not accept the default without checking it
  matches the original Access cascade rule.
- Access unique indexes → Dataverse **alternate keys**.
- Access table-level validation rules → Dataverse **business rules** or
  plugins (server-side, authoritative) — supplement with TypeScript-side
  validation in the Code App for immediate UX feedback, but treat Dataverse
  as the source of truth.
- Access multi-value lookup fields → a genuine Dataverse N:N relationship,
  never a delimited text column.
