# Congress Entity Structure

This directory contains TOML files for Philippine Congress entities. Each file
represents a single Congress entity with comprehensive metadata about its
duration and identification.

## Required Fields

| Field                  | Type    | Description                      | Example                              |
| ---------------------- | ------- | -------------------------------- | ------------------------------------ |
| `id`                   | string  | Unique identifier (ULID format)  | `"01K5S4AG1AJZ79AMDYG4MFHE7M"`       |
| `congress_number`      | integer | Official congress number         | `14`                                 |
| `congress_website_key` | integer | Key used on the congress website | `14`                                 |
| `ordinal`              | string  | Ordinal representation           | `"14th"`                             |
| `name`                 | string  | Full official name               | `"14th Congress of the Philippines"` |
| `start_date`           | string  | Start date (ISO format)          | `"2007-07-23"`                       |
| `start_year`           | integer | Starting year                    | `2007`                               |
| `year_range`           | string  | Year range representation        | `"2007-2010"` or `"2025-present"`    |

## Optional Fields

| Field      | Type    | Description                             | Example        |
| ---------- | ------- | --------------------------------------- | -------------- |
| `end_date` | string  | End date (ISO format) - omit if ongoing | `"2010-06-09"` |
| `end_year` | integer | Ending year - omit if ongoing           | `2010`         |

## Example

```toml
id = "01K5S4AG1AJZ79AMDYG4MFHE7M"
congress_number = 14
congress_website_key = 14
ordinal = "14th"
name = "14th Congress of the Philippines"
start_date = "2007-07-23"
start_year = 2007
end_date = "2010-06-09"
end_year = 2010
year_range = "2007-2010"
```

## Congress Number Mapping

The `.congress-number-mapping.yml` file provides a quick lookup between congress
numbers and their corresponding IDs:

```yaml
14: 01K5S4AG1AJZ79AMDYG4MFHE7M
15: 01K5S4AG1AJZ79AMDYG4MFHE7N
# ... and so on
```

## Notes

- Congress nodes serve as central entities in the graph database
- Committees and People are linked to Congress nodes via relationships
- The data covers the 8th through 20th Congress of the Philippines
- Additional fields can be added as needed and will be automatically included in
  the database sync
