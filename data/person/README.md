# Person Entity Structure

This directory contains TOML files for senators and other officials in the
Philippine Congress. Each file represents a single Person entity with their
metadata and the congresses where they served.

## Required Fields

| Field                 | Type   | Description                              | Example                             |
| --------------------- | ------ | ---------------------------------------- | ----------------------------------- |
| `id`                  | string | Unique identifier (ULID format)          | `"01K5S1TKQXA0NWQD2GJS73BEKS"`      |
| `senate_website_keys` | array  | Keys used on the Senate website          | `["ABENI"]` or `["ZJMIG", "ZMIGU"]` |
| `full_name`           | string | Complete name as displayed               | `"Aquino III, Benigno S."`          |
| `last_name`           | string | Family/surname                           | `"Aquino"`                          |
| `first_name`          | string | Given name(s)                            | `"Benigno"`                         |
| `congresses`          | array  | Congress numbers where the person served | `[14, 15, 16]`                      |

## Optional Fields

| Field            | Type   | Description                       | Example             |
| ---------------- | ------ | --------------------------------- | ------------------- |
| `middle_initial` | string | Middle initial                    | `"S"`               |
| `name_suffix`    | string | Name suffix (Jr., Sr., III, etc.) | `"III"`             |
| `name_prefix`    | string | Name prefix (Dr., Hon., etc.)     | `"Dr."`             |
| `aliases`        | array  | Nicknames or alternative names    | `["Sonny", "Chiz"]` |

## Examples

### Basic Person Entry

```toml
id = "01K5S1TKQYXMDG8MDDP8E0XX0K"
senate_website_keys = ["BAQUI"]
full_name = "Aquino, Bam"
last_name = "Aquino"
first_name = "Bam"
congresses = [20]
```

### Person with Multiple Website Keys

```toml
id = "01K5S6MAZ4YBST5GDJV827A0K9"
senate_website_keys = ["ZJMIG", "ZMIGU"]
full_name = "Zubiri, Juan Miguel F."
last_name = "Zubiri"
middle_initial = "F"
first_name = "Juan Miguel"
congresses = [14, 15, 17, 18, 19, 20]
```

### Person with Optional Fields

```toml
id = "01K5S1TKR4KBTJ6Z81S0Y4A055"
senate_website_keys = ["TANTO"]
full_name = "Trillanes IV, Antonio \"Sonny\" F."
aliases = ["Sonny"]
name_suffix = "IV"
last_name = "Trillanes"
middle_initial = "F"
first_name = "Antonio"
congresses = [14, 15, 16, 17]
```

## Notes

- The `senate_website_keys` field is an array to handle cases where a person has
  multiple keys on the Senate website (e.g., different keys across different
  congresses or name changes)
- The `congresses` field determines which Congress nodes this person will be
  linked to in the graph database
- Names should match official Senate records
- The `aliases` field is useful for storing commonly used nicknames
- Additional fields can be added as needed and will be automatically included in
  the database sync
- The sync script dynamically includes all fields except `congresses` as node
  properties (the `congresses` array is only used to create relationships)
