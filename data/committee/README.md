# Committee Entity Structure

This directory contains TOML files for Philippine Senate Committee entities.
Each file represents a single Committee entity with its metadata and the
congresses where it was active.

## Required Fields

| Field                 | Type   | Description                     | Example                                                   |
| --------------------- | ------ | ------------------------------- | --------------------------------------------------------- |
| `id`                  | string | Unique identifier (ULID format) | `"01K5S1TKR6C8VJ3WHGSVFV7MS2"`                            |
| `senate_website_keys` | array  | Keys used on the Senate website | `["ABSVO"]`                                               |
| `name`                | string | Official committee name         | `"Absentee Voting"`                                       |
| `type`                | string | Committee classification        | `"regular"`, `"subcommittee"`, `"oversight"`, `"special"` |
| `congresses`          | array  | Congress numbers where active   | `[14, 15, 16]`                                            |

## Committee Types

- **regular**: Standing committees
- **subcommittee**: Specialized subcommittees under main committees
- **oversight**: Congressional oversight committees
- **special**: Special or ad-hoc committees

## Example

```toml
id = "01K5S6MAZAHEE159XQJ0EQ84ZD"
senate_website_keys = ["ABSVO"]
name = "Absentee Voting"
type = "regular"
congresses = [14]
```

## Notes

- The `congresses` field determines which Congress nodes this committee will be
  linked to in the graph database
- Committee names should match the official Senate designation
- Additional fields can be added as needed and will be automatically included in
  the database sync
