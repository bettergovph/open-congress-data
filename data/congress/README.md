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

## Database Relationships

Congress nodes serve as the top-level entities in the graph database with the following incoming relationships:

### Incoming Relationships

- `(Chamber)-[:BELONGS_TO]->(Congress)` - Senate and House chambers for this congress
- `(Committee)-[:BELONGS_TO]->(Congress)` - Committees that operated in this congress

### No Direct Person Relationships

**Important:** There are NO direct relationships from Person to Congress nodes. All person-congress connections go through Chamber nodes:
- Person → MEMBER_OF → Chamber → BELONGS_TO → Congress

## Relationship Hierarchy

```
        Congress
           ↑
           | BELONGS_TO
           |
    ┌──────┴──────┐
    |             |
 Chamber      Committee
(Senate/House)
    ↑
    | MEMBER_OF
    |
  Person
```

## Query Examples

### Find All Chambers for a Congress
```cypher
MATCH (c:Congress {congress_number: 14})<-[:BELONGS_TO]-(g:Group {type: "chamber"})
RETURN c.name, g.name, g.subtype
```

### Find All Committees in a Congress
```cypher
MATCH (c:Congress {congress_number: 20})<-[:BELONGS_TO]-(com:Committee)
RETURN c.name, com.name, com.type
```

### Find All People Who Served in a Congress (via Chambers)
```cypher
MATCH (c:Congress {congress_number: 19})<-[:BELONGS_TO]-(g:Group {type: "chamber"})<-[:MEMBER_OF]-(p:Person)
RETURN c.name, g.subtype as chamber, p.first_name, p.last_name
ORDER BY g.subtype, p.last_name
```

### Count Members by Chamber for Each Congress
```cypher
MATCH (c:Congress)<-[:BELONGS_TO]-(g:Group {type: "chamber"})<-[:MEMBER_OF]-(p:Person)
RETURN c.ordinal, g.subtype as chamber, COUNT(DISTINCT p) as member_count
ORDER BY c.congress_number, g.subtype
```

## Congress Number Mapping

The `.congress-number-mapping.yml` file provides a quick lookup between congress
numbers and their corresponding IDs:

```yaml
14: 01K5S4AG1AJZ79AMDYG4MFHE7M
15: 01K5S4AG1AJZ79AMDYG4MFHE7N
# ... and so on
```

## Data Coverage

The dataset includes congress entities from:
- **8th Congress** (1987-1992) - First congress after the 1987 Constitution
- Through **20th Congress** (2025-2028) - Current congress

Each congress has:
- One Congress entity file
- Two Chamber entities (Senate and House) in `data/group/chamber/`
- Multiple Committee entities in `data/committee/`
- Person entities with memberships linking to the chambers

## Notes

- Congress nodes serve as the top-level entities in the graph database
- Each congress represents a 3-year term
- The bicameral structure is represented through Chamber (Group) nodes
- Committees and Chambers are linked to Congress nodes via BELONGS_TO relationships
- People are linked to Chambers (not directly to Congress) via MEMBER_OF relationships
- The data covers the 8th through 20th Congress of the Philippines
- Additional fields can be added as needed and will be automatically included in the database sync