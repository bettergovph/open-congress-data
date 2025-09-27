# Chamber Entity Structure

This directory contains TOML files for the chambers (Senate and House of Representatives) of each Philippine Congress. Each file represents a specific chamber for a specific congress session.

## Overview

The Philippine Congress follows a bicameral system with two chambers:
- **Senate** - The upper chamber with 24 senators
- **House of Representatives** - The lower chamber with district and party-list representatives

Each congress session (8th through 20th) has separate files for its Senate and House chambers.

## File Naming Convention

Files are named using ULID format identifiers. Each congress has two files:
- One for the Senate chamber
- One for the House of Representatives chamber

## Required Fields

| Field     | Type    | Description                                      | Example                              |
| --------- | ------- | ------------------------------------------------ | ------------------------------------ |
| `id`      | string  | Unique identifier (ULID format)                 | `"01K64ECAES8JBV2Y5HR437SBSX"`      |
| `name`    | string  | Display name of the chamber                     | `"Senate - 8th Congress"`            |
| `type`    | string  | Entity type (always "chamber")                  | `"chamber"`                          |
| `subtype` | string  | Chamber type                                    | `"senate"` or `"house"`              |
| `congress`| integer | Congress number this chamber belongs to         | `8` through `20`                     |

## Example Files

### Senate Chamber
```toml
id = "01K64ECAES8JBV2Y5HR437SBSX"
name = "Senate - 8th Congress"
type = "chamber"
subtype = "senate"
congress = 8
```

### House of Representatives Chamber
```toml
id = "01K64ECAETF9923DENHPM8G71R"
name = "House of Representatives - 8th Congress"
type = "chamber"
subtype = "house"
congress = 8
```

## Database Relationships

Chamber nodes in the Neo4j database have the following relationships:

### Incoming Relationships
- `(Person)-[:MEMBER_OF]->(Chamber)` - People who served in this chamber

### Outgoing Relationships
- `(Chamber)-[:BELONGS_TO]->(Congress)` - Links the chamber to its congress session

## Relationship Hierarchy

```
Congress (e.g., "8th Congress")
    ↑
    | BELONGS_TO
    |
Chamber (e.g., "Senate - 8th Congress")
    ↑
    | MEMBER_OF
    |
Person (e.g., senators/representatives)
```

## Query Examples

### Find All Senate Chambers
```cypher
MATCH (g:Group {type: "chamber", subtype: "senate"})
RETURN g.name, g.congress
ORDER BY g.congress
```

### Find Members of a Specific Chamber
```cypher
MATCH (p:Person)-[:MEMBER_OF]->(g:Group {type: "chamber", subtype: "senate", congress: 20})
RETURN p.first_name, p.last_name
ORDER BY p.last_name
```

### Find Which Congress a Chamber Belongs To
```cypher
MATCH (g:Group {type: "chamber", congress: 15})-[:BELONGS_TO]->(c:Congress)
RETURN g.name, c.name, c.year_range
```

## Data Coverage

The dataset includes chambers for the following congresses:

| Congress | Years      | Senate | House |
| -------- | ---------- | ------ | ----- |
| 8th      | 1987-1992  | ✓      | ✓     |
| 9th      | 1992-1995  | ✓      | ✓     |
| 10th     | 1995-1998  | ✓      | ✓     |
| 11th     | 1998-2001  | ✓      | ✓     |
| 12th     | 2001-2004  | ✓      | ✓     |
| 13th     | 2004-2007  | ✓      | ✓     |
| 14th     | 2007-2010  | ✓      | ✓     |
| 15th     | 2010-2013  | ✓      | ✓     |
| 16th     | 2013-2016  | ✓      | ✓     |
| 17th     | 2016-2019  | ✓      | ✓     |
| 18th     | 2019-2022  | ✓      | ✓     |
| 19th     | 2022-2025  | ✓      | ✓     |
| 20th     | 2025-2028  | ✓      | ✓     |

## Notes

- Each congress must have exactly two chamber files (Senate and House)
- The `type` field must always be `"chamber"` for proper database queries
- The `subtype` field must be either `"senate"` or `"house"`
- The `congress` field must match an existing Congress entity's `congress_number`
- Chamber nodes serve as the connection point between Person and Congress entities
- This structure accurately represents the bicameral nature of the Philippine Congress

## Adding New Chambers

When adding chambers for a new congress:

1. Create two new TOML files with unique ULID identifiers
2. Set the `congress` field to the new congress number
3. Use consistent naming: `"Senate - Nth Congress"` and `"House of Representatives - Nth Congress"`
4. Ensure the corresponding Congress entity exists in `data/congress/`
5. Update Person entities' `memberships` arrays to reference the new chambers