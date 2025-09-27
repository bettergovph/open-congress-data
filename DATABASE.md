# Neo4j Database Schema Documentation

This document describes the structure of the Neo4j graph database that stores Philippine Congress data. The database is populated by the `scripts/sync_to_neo4j.py` script from TOML files in the `data/` directory.

## Overview

The database uses a graph model to represent the relationships between Congress sessions, chambers (Senate/House), committees, and people (senators and representatives). This structure allows for efficient querying of complex relationships like chamber memberships across different congresses and tracking of political careers over time.

## Node Types

### 1. Congress Node

Represents a session of the Philippine Congress.

**Label:** `Congress`

**Properties:**
- `id` (string, required) - Unique identifier (ULID format)
- `congress_number` (integer, required) - Numeric identifier (e.g., 8, 14, 20)
- `congress_website_key` (integer) - Key used on official congress websites
- `name` (string) - Full name (e.g., "8th Congress of the Philippines")
- `ordinal` (string) - Ordinal representation (e.g., "8th", "14th", "20th")
- `start_date` (string) - ISO date when congress began (YYYY-MM-DD)
- `end_date` (string) - ISO date when congress ended (YYYY-MM-DD)
- `start_year` (integer) - Year congress began
- `end_year` (integer) - Year congress ended
- `year_range` (string) - Date range (e.g., "1987-1992")

**Example Cypher Query:**
```cypher
MATCH (c:Congress {congress_number: 20})
RETURN c
```

### 2. Group Node (Chambers)

Represents chambers (Senate or House of Representatives) within a specific Congress.

**Label:** `Group`

**Properties:**
- `id` (string, required) - Unique identifier (ULID format)
- `name` (string, required) - Chamber name (e.g., "Senate - 8th Congress")
- `type` (string, required) - Always "chamber" for chamber groups
- `subtype` (string, required) - Either "senate" or "house"
- `congress` (integer, required) - Congress number this chamber belongs to

**Example Cypher Query:**
```cypher
// Find all Senate chambers
MATCH (g:Group {type: "chamber", subtype: "senate"})
RETURN g.name, g.congress
ORDER BY g.congress

// Find House chamber for 19th Congress
MATCH (g:Group {type: "chamber", subtype: "house", congress: 19})
RETURN g
```

### 3. Committee Node

Represents a Senate or House committee within a Congress.

**Label:** `Committee`

**Properties:**
- `id` (string, required) - Unique identifier (ULID format)
- `name` (string, required) - Committee name
- `type` (string) - Committee type (e.g., "regular", "special")
- `senate_website_keys` (array of strings) - Keys used on Senate website

**Example Cypher Query:**
```cypher
MATCH (com:Committee)
WHERE com.name CONTAINS "Finance"
RETURN com
```

### 4. Person Node

Represents senators, representatives, and other congressional officials.

**Label:** `Person`

**Properties:**
- `id` (string, required) - Unique identifier (ULID format)
- `first_name` (string, 99.9% frequency) - Given name
- `last_name` (string, 99.9% frequency) - Surname
- `middle_name` (string, 92.2% frequency) - Middle name
- `name_prefix` (string, 0.3% frequency) - Name prefix (e.g., "Atty", "Dr")
- `name_suffix` (string, 15.8% frequency) - Name suffix (e.g., "Jr", "III")
- `professional_designations` (array of strings, 2.2% frequency) - Professional titles (e.g., ["RN"], ["MD"])
- `senate_website_keys` (array of strings, 5% frequency) - Keys used on Senate website for senators
- `congress_website_primary_keys` (array of integers, 96.6% frequency) - Primary keys used on Congress website
- `congress_website_author_keys` (array of strings, 96.6% frequency) - Author keys used on Congress website (e.g., ["G090"])
- `aliases` (array of strings, 39% frequency) - Alternative names or nicknames

**Example Cypher Query:**
```cypher
MATCH (p:Person)
WHERE p.last_name = "Aquino"
RETURN p
```

## Relationships

### 1. MEMBER_OF

Connects people to the chambers they served in.

**Direction:** `(Person)-[:MEMBER_OF]->(Group)`

**Properties:**
- `position` (string) - Additional position details if any

**Example Cypher Query:**
```cypher
// Find all senators in 20th Congress
MATCH (p:Person)-[:MEMBER_OF]->(g:Group {type: "chamber", subtype: "senate", congress: 20})
RETURN p.last_name, p.first_name
ORDER BY p.last_name

// Find all House members in 19th Congress
MATCH (p:Person)-[:MEMBER_OF]->(g:Group {type: "chamber", subtype: "house", congress: 19})
RETURN p.last_name, p.first_name
ORDER BY p.last_name
```

### 2. BELONGS_TO

Connects chambers and committees to the congresses they operated in.

**Direction:**
- `(Group)-[:BELONGS_TO]->(Congress)` for chambers
- `(Committee)-[:BELONGS_TO]->(Congress)` for committees

**Properties:** None

**Example Cypher Query:**
```cypher
// Find Senate chamber for 20th Congress
MATCH (g:Group {type: "chamber", subtype: "senate"})-[:BELONGS_TO]->(c:Congress {congress_number: 20})
RETURN g, c

// Find all committees in 20th Congress
MATCH (com:Committee)-[:BELONGS_TO]->(con:Congress {congress_number: 20})
RETURN com.name, con.name
```

## Relationship Hierarchy

The database follows this hierarchy:
```
Congress
    ↑
    | (BELONGS_TO)
    |
  Group (Chamber)
    ↑
    | (MEMBER_OF)
    |
  Person

Congress
    ↑
    | (BELONGS_TO)
    |
  Committee
```

**Important:** There are NO direct relationships from Person to Congress. All person-congress connections go through the chamber (Group) nodes.

## Indexes

The following indexes are created for optimized query performance:

1. **Congress Indexes:**
   - `(Congress).id`
   - `(Congress).congress_number`

2. **Group Indexes:**
   - `(Group).id`
   - `(Group).type`
   - `(Group).congress`

3. **Committee Indexes:**
   - `(Committee).id`
   - `(Committee).name`

4. **Person Indexes:**
   - `(Person).id`
   - `(Person).full_name`
   - `(Person).last_name`

## Common Query Patterns

### Find all senators in a specific congress
```cypher
MATCH (p:Person)-[:MEMBER_OF]->(g:Group {type: "chamber", subtype: "senate", congress: 20})
RETURN p.last_name, p.first_name
ORDER BY p.last_name
```

### Find which chamber a person served in for each congress
```cypher
MATCH (p:Person {last_name: "Aquino"})-[:MEMBER_OF]->(g:Group)-[:BELONGS_TO]->(c:Congress)
RETURN p.first_name, p.last_name, g.subtype as chamber, c.ordinal
ORDER BY c.congress_number
```

### Count senators vs representatives by congress
```cypher
MATCH (g:Group {type: "chamber"})-[:BELONGS_TO]->(c:Congress)
MATCH (p:Person)-[:MEMBER_OF]->(g)
RETURN c.ordinal, g.subtype as chamber, COUNT(DISTINCT p) as member_count
ORDER BY c.congress_number, g.subtype
```

### Find committees a person might be associated with in a congress
```cypher
MATCH (p:Person {last_name: "Angara"})-[:MEMBER_OF]->(g:Group)-[:BELONGS_TO]->(c:Congress)
MATCH (com:Committee)-[:BELONGS_TO]->(c)
RETURN DISTINCT com.name, c.ordinal
```

### Search for person by senate website key
```cypher
MATCH (p:Person)
WHERE "ABENI" IN p.senate_website_keys
RETURN p
```

### Find all congresses a person served in
```cypher
MATCH (p:Person {last_name: "Aquino", first_name: "Benigno"})-[:MEMBER_OF]->(g:Group)-[:BELONGS_TO]->(c:Congress)
RETURN c.ordinal, g.subtype as chamber
ORDER BY c.congress_number
```

### Get complete chamber membership for a congress
```cypher
// Get all Senate members for 20th Congress
MATCH (c:Congress {congress_number: 20})<-[:BELONGS_TO]-(g:Group {type: "chamber", subtype: "senate"})<-[:MEMBER_OF]-(p:Person)
RETURN p.last_name, p.first_name
ORDER BY p.last_name

// Get all House members for 20th Congress
MATCH (c:Congress {congress_number: 20})<-[:BELONGS_TO]-(g:Group {type: "chamber", subtype: "house"})<-[:MEMBER_OF]-(p:Person)
RETURN p.last_name, p.first_name
ORDER BY p.last_name
```

## Data Import Process

The database is populated by `scripts/sync_to_neo4j.py` which:

1. Reads TOML files from:
   - `data/congress/*.toml` - Congress entities
   - `data/group/chamber/*.toml` - Chamber (Senate/House) entities
   - `data/committee/*.toml` - Committee entities
   - `data/person/*.toml` - Person entities

2. Creates nodes with MERGE operations (create if not exists, update if exists)

3. Establishes relationships based on:
   - Chamber TOML files contain `congress` field → creates BELONGS_TO relationships to Congress
   - Committee TOML files contain `congresses` array → creates BELONGS_TO relationships to Congress
   - Person TOML files contain `memberships` array with chamber details → creates MEMBER_OF relationships to appropriate Group nodes

4. Creates indexes for optimized querying

## Membership Structure in Person TOML Files

Person files contain a `memberships` array that defines their chamber affiliations:

```toml
[[memberships]]
type = "chamber"
congress = 15
subtype = "house"  # or "senate"

[[memberships]]
type = "chamber"
congress = 16
subtype = "senate"
```

This structure creates MEMBER_OF relationships to the corresponding chamber Group nodes.

## Connection Configuration

The sync script requires the following environment variables:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

## REST API Usage

External REST APIs can query this database using the Neo4j driver for their respective language. The graph structure allows for:

- Efficient traversal of relationships
- Complex filtering across multiple entity types
- Aggregation queries for statistics
- Full-text search on indexed properties
- Clear separation between chambers (Senate/House)

## Notes for API Development

1. **Array Properties:** Properties like `senate_website_keys` and `aliases` are stored as arrays. Use the `IN` operator to search within them.

2. **Optional Properties:** Not all properties are present on all nodes. Always handle potential null values in your queries.

3. **Chamber Navigation:** To find which congress a person served in, you must traverse through the Group (chamber) node:
   - Person → MEMBER_OF → Group → BELONGS_TO → Congress

4. **Performance:** Use indexed properties in WHERE clauses when possible for optimal query performance.

5. **Data Consistency:** The MERGE operations ensure no duplicate nodes are created based on the `id` property.

6. **Chamber Types:** Always filter Group nodes by `type: "chamber"` when looking for Senate/House chambers, as the Group label may be used for other entity types in the future.