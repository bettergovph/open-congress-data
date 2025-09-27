# Person Entity Structure

This directory contains TOML files for senators and representatives in the
Philippine Congress. Each file represents a single Person entity with their
metadata and chamber memberships.

## Required Fields

| Field                 | Type   | Description                              | Example                             |
| --------------------- | ------ | ---------------------------------------- | ----------------------------------- |
| `id`                  | string | Unique identifier (ULID format)          | `"01K5S1TKQXA0NWQD2GJS73BEKS"`      |
| `last_name`           | string | Family/surname                           | `"Aquino"`                          |
| `first_name`          | string | Given name(s)                            | `"Benigno"`                         |
| `memberships`         | array  | Chamber memberships (see below)          | See membership examples below        |

## Optional Fields

| Field                              | Type   | Description                            | Example                      |
| ---------------------------------- | ------ | -------------------------------------- | ---------------------------- |
| `middle_name`                      | string | Middle name                            | `"Santos"`                   |
| `name_suffix`                      | string | Name suffix (Jr., Sr., III, etc.)      | `"III"`                      |
| `name_prefix`                      | string | Name prefix (Dr., Hon., etc.)          | `"Dr."`                      |
| `aliases`                          | array  | Nicknames or alternative names         | `["Sonny", "Chiz"]`          |
| `senate_website_keys`              | array  | Keys used on the Senate website        | `["ABENI", "ZMIGU"]`         |
| `congress_website_primary_keys`    | array  | Primary keys on Congress website       | `[1234, 5678]`               |
| `congress_website_author_keys`     | array  | Author keys on Congress website        | `["G090", "G091"]`           |
| `professional_designations`        | array  | Professional titles                    | `["MD", "RN"]`               |

## Membership Structure

The `memberships` array defines which chambers (Senate or House) a person served in for specific congresses. Each membership entry contains:

| Field     | Type   | Required | Description                         | Values                    |
| --------- | ------ | -------- | ----------------------------------- | ------------------------- |
| `type`    | string | Yes      | Type of membership                  | `"chamber"`               |
| `congress`| integer| Yes      | Congress number                     | `8` through `20`          |
| `subtype` | string | Yes      | Chamber type                        | `"senate"` or `"house"`   |
| `position`| string | No       | Additional position/role details    | Any string                |

### Membership Examples

#### Senator in Single Congress
```toml
[[memberships]]
type = "chamber"
congress = 20
subtype = "senate"
```

#### Representative Who Became Senator
```toml
# Served in House for 15th Congress
[[memberships]]
type = "chamber"
congress = 15
subtype = "house"

# Moved to Senate for 16th Congress
[[memberships]]
type = "chamber"
congress = 16
subtype = "senate"

# Continued in Senate for 17th Congress
[[memberships]]
type = "chamber"
congress = 17
subtype = "senate"
```

#### Person Who Served in Multiple Congresses
```toml
[[memberships]]
type = "chamber"
congress = 14
subtype = "senate"

[[memberships]]
type = "chamber"
congress = 15
subtype = "senate"

[[memberships]]
type = "chamber"
congress = 17
subtype = "senate"

# Note: Missing congress 16 means they didn't serve in that congress
```

## Complete Example Files

### Basic Senator
```toml
id = "01K5S1TKQYXMDG8MDDP8E0XX0K"
first_name = "Bam"
last_name = "Aquino"
senate_website_keys = ["BAQUI"]

[[memberships]]
type = "chamber"
congress = 16
subtype = "senate"

[[memberships]]
type = "chamber"
congress = 17
subtype = "senate"
```

### Representative with Full Details
```toml
id = "01K5S1TKR4KBTJ6Z81S0Y4A055"
first_name = "Juan"
middle_name = "Ponce"
last_name = "Enrile"
name_suffix = "Jr"
aliases = ["Johnny"]
congress_website_primary_keys = [1234]
congress_website_author_keys = ["G090"]

[[memberships]]
type = "chamber"
congress = 18
subtype = "house"

[[memberships]]
type = "chamber"
congress = 19
subtype = "house"
```

### Person Who Moved Between Chambers
```toml
id = "01K5S6MAZ4YBST5GDJV827A0HN"
first_name = "Alan Peter"
middle_name = "S"
last_name = "Cayetano"
senate_website_keys = ["ACAYE", "APCAY"]

# Started in House
[[memberships]]
type = "chamber"
congress = 13
subtype = "house"

# Moved to Senate
[[memberships]]
type = "chamber"
congress = 14
subtype = "senate"

[[memberships]]
type = "chamber"
congress = 15
subtype = "senate"

# Returned to House
[[memberships]]
type = "chamber"
congress = 18
subtype = "house"
```

## Database Relationships

The membership structure creates the following relationships in the Neo4j database:

1. Each membership creates a `MEMBER_OF` relationship from the Person to a Chamber (Group) node
2. The Chamber is identified by matching:
   - `type: "chamber"`
   - `congress: <number>`
   - `subtype: "senate"` or `"house"`
3. There are NO direct relationships from Person to Congress nodes

This structure allows tracking:
- Politicians who served in different chambers across different congresses
- Career progressions from House to Senate (or vice versa)
- Gaps in service (missing congress numbers)

## Notes

- The `memberships` array replaces the old `congresses` array
- Each person must have at least one membership entry
- The sync script uses the membership data to create proper relationships to Chamber nodes
- Additional fields can be added as needed and will be automatically included in the database sync
- All fields except `memberships` are stored as node properties in the database