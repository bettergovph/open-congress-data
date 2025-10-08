# JanusGraph Database Schema Documentation

This document describes the structure of the JanusGraph graph database that stores Philippine Congress data. The database is populated by the `scripts/sync_to_janusgraph.py` script from TOML files in the `data/` directory.

## Overview

The database uses a graph model powered by JanusGraph to represent the relationships between Congress sessions, chambers (Senate/House), committees, and people (senators and representatives). This structure allows for efficient querying of complex relationships and horizontal scalability as the dataset grows.

## Why JanusGraph?

- **Horizontal Scalability**: Distributed architecture supports massive datasets
- **Multiple Storage Backends**: ScyllaDB, Cassandra, HBase, or BerkeleyDB
- **TinkerPop/Gremlin**: Industry-standard graph query language
- **Open Source**: No licensing restrictions
- **Full-text Search**: Elasticsearch integration for advanced text queries

## Vertex Types (Nodes)

### 1. Congress Vertex

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

**Example Gremlin Query:**
```groovy
// Find 20th Congress
g.V().hasLabel('Congress').has('congress_number', 20)

// Get all congresses
g.V().hasLabel('Congress').valueMap()
```

### 2. Group Vertex (Chambers)

Represents chambers (Senate or House of Representatives) within a specific Congress.

**Label:** `Group`

**Properties:**
- `id` (string, required) - Unique identifier (ULID format)
- `name` (string, required) - Chamber name (e.g., "Senate - 8th Congress")
- `type` (string, required) - Always "chamber" for chamber groups
- `subtype` (string, required) - Either "senate" or "house"
- `congress` (integer, required) - Congress number this chamber belongs to

**Example Gremlin Query:**
```groovy
// Find all Senate chambers
g.V().hasLabel('Group').has('type', 'chamber').has('subtype', 'senate').valueMap()

// Find House chamber for 19th Congress
g.V().hasLabel('Group')
  .has('type', 'chamber')
  .has('subtype', 'house')
  .has('congress', 19)
```

### 3. Committee Vertex

Represents a Senate or House committee within a Congress.

**Label:** `Committee`

**Properties:**
- `id` (string, required) - Unique identifier (ULID format)
- `name` (string, required) - Committee name
- `type` (string) - Committee type (e.g., "regular", "special")

**Example Gremlin Query:**
```groovy
// Find committees with "Finance" in the name
g.V().hasLabel('Committee').has('name', containing('Finance')).valueMap()

// Count all committees
g.V().hasLabel('Committee').count()
```

### 4. Person Vertex

Represents senators, representatives, and other congressional officials.

**Label:** `Person`

**Properties:**
- `id` (string, required) - Unique identifier (ULID format)
- `first_name` (string) - Given name
- `last_name` (string) - Surname
- `middle_name` (string) - Middle name
- `name_prefix` (string) - Name prefix (e.g., "Atty", "Dr")
- `name_suffix` (string) - Name suffix (e.g., "Jr", "III")

**Example Gremlin Query:**
```groovy
// Find person by last name
g.V().hasLabel('Person').has('last_name', 'Aquino').valueMap()

// Find all people
g.V().hasLabel('Person').values('first_name', 'last_name')
```

### 5. Document Vertex

Represents legislative documents such as House Bills (HB) and Senate Bills (SB).

**Label:** `Document`

**Properties:**
- `id` (string, required) - Unique identifier (ULID format)
- `type` (string) - Document type (e.g., "bill")
- `subtype` (string) - Document subtype ("HB" for House Bills, "SB" for Senate Bills)
- `name` (string) - Document name/identifier (e.g., "HBN-00001", "SBN-00001")
- `bill_number` (integer) - Numeric bill number (e.g., 1, 59, 1000)
- `congress` (integer) - Congress number when filed
- `title` (string) - Short title of the bill
- `date_filed` (string) - Date when the bill was filed (YYYY-MM-DD)
- `long_title` (string) - Full descriptive title of the bill
- `scope` (string) - Scope of the bill (e.g., "National", "Local")
- `authors_raw` (string) - Raw author information from source

**Example Gremlin Query:**
```groovy
// Find all Senate Bills in 19th Congress
g.V().hasLabel('Document')
  .has('subtype', 'SB')
  .has('congress', 19)
  .order().by('bill_number')
  .valueMap('bill_number', 'title')

// Find House Bill 59 in 18th Congress
g.V().hasLabel('Document')
  .has('subtype', 'HB')
  .has('congress', 18)
  .has('bill_number', 59)
```

## Edge Types (Relationships)

### 1. MEMBER_OF

Connects people to the chambers they served in.

**Direction:** `(Person)-[MEMBER_OF]->(Group)`

**Properties:**
- `position` (string) - Additional position details if any

**Example Gremlin Query:**
```groovy
// Find all senators in 20th Congress
g.V().hasLabel('Group')
  .has('type', 'chamber')
  .has('subtype', 'senate')
  .has('congress', 20)
  .in('MEMBER_OF')
  .hasLabel('Person')
  .values('last_name', 'first_name')

// Find all House members in 19th Congress
g.V().hasLabel('Group')
  .has('type', 'chamber')
  .has('subtype', 'house')
  .has('congress', 19)
  .in('MEMBER_OF')
  .hasLabel('Person')
  .values('last_name', 'first_name')
```

### 2. BELONGS_TO

Connects chambers and committees to the congresses they operated in.

**Direction:**
- `(Group)-[BELONGS_TO]->(Congress)` for chambers
- `(Committee)-[BELONGS_TO]->(Congress)` for committees

**Properties:** None

**Example Gremlin Query:**
```groovy
// Find Senate chamber for 20th Congress
g.V().hasLabel('Congress')
  .has('congress_number', 20)
  .in('BELONGS_TO')
  .hasLabel('Group')
  .has('type', 'chamber')
  .has('subtype', 'senate')

// Find all committees in 20th Congress
g.V().hasLabel('Congress')
  .has('congress_number', 20)
  .in('BELONGS_TO')
  .hasLabel('Committee')
  .values('name')
```

### 3. AUTHORED

Connects people to the documents they authored (both House Bills and Senate Bills).

**Direction:** `(Person)-[AUTHORED]->(Document)`

**Properties:** None

**How authorship is determined:**
- **Senate Bills:** Uses `meta.senate_website_author_codes` mapped via `data/person/.senate-website-key-mapping.yml`
- **House Bills:** Uses `meta.congress_website_author_codes` mapped via `data/person/.house-website-key-mapping.yml`

**Example Gremlin Query:**
```groovy
// Find all bills authored by a specific person
g.V().hasLabel('Person')
  .has('last_name', 'Marcos')
  .out('AUTHORED')
  .valueMap('subtype', 'bill_number', 'title')

// Find authors of a specific House Bill
g.V().hasLabel('Document')
  .has('subtype', 'HB')
  .has('congress', 18)
  .has('bill_number', 59)
  .in('AUTHORED')
  .values('last_name', 'first_name')

// Count bills authored by person
g.V().hasLabel('Person')
  .has('last_name', 'Aquino')
  .out('AUTHORED')
  .count()
```

### 4. FILED_IN

Connects documents to the congress they were filed in.

**Direction:** `(Document)-[FILED_IN]->(Congress)`

**Properties:** None

**Example Gremlin Query:**
```groovy
// Find all bills filed in 19th Congress
g.V().hasLabel('Congress')
  .has('congress_number', 19)
  .in('FILED_IN')
  .hasLabel('Document')
  .valueMap('bill_number', 'title', 'subtype')

// Count bills by congress
g.V().hasLabel('Congress')
  .project('congress', 'bill_count')
    .by('ordinal')
    .by(__.in('FILED_IN').count())
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
    |
    | (AUTHORED)
    ↓
  Document
    |
    | (FILED_IN)
    ↓
  Congress

Congress
    ↑
    | (BELONGS_TO)
    |
  Committee
```

**Important:**
- There are NO direct relationships from Person to Congress. All person-congress connections go through the chamber (Group) vertices.
- Documents are connected to Congress via FILED_IN edges
- Documents are connected to their authors (Person vertices) via AUTHORED edges

## Indexes

The following indexes are created for optimized query performance:

1. **Congress Indexes:**
   - `id` (composite index)

2. **Group Indexes:**
   - `id` (composite index)

3. **Committee Indexes:**
   - `id` (composite index)

4. **Person Indexes:**
   - `id` (composite index)

5. **Document Indexes:**
   - `id` (composite index)

## Common Query Patterns

### Find all senators in a specific congress
```groovy
g.V().hasLabel('Group')
  .has('type', 'chamber')
  .has('subtype', 'senate')
  .has('congress', 20)
  .in('MEMBER_OF')
  .values('last_name', 'first_name')
  .order()
```

### Find which chamber a person served in for each congress
```groovy
g.V().hasLabel('Person')
  .has('last_name', 'Aquino')
  .out('MEMBER_OF')
  .as('chamber')
  .out('BELONGS_TO')
  .as('congress')
  .select('chamber', 'congress')
  .by('subtype')
  .by('ordinal')
```

### Count senators vs representatives by congress
```groovy
g.V().hasLabel('Congress')
  .project('congress', 'senate_count', 'house_count')
    .by('ordinal')
    .by(__.in('BELONGS_TO')
          .has('subtype', 'senate')
          .in('MEMBER_OF')
          .count())
    .by(__.in('BELONGS_TO')
          .has('subtype', 'house')
          .in('MEMBER_OF')
          .count())
```

### Find all congresses a person served in
```groovy
g.V().hasLabel('Person')
  .has('last_name', 'Aquino')
  .has('first_name', 'Benigno')
  .out('MEMBER_OF')
  .as('chamber')
  .out('BELONGS_TO')
  .project('congress', 'chamber')
    .by('ordinal')
    .by(select('chamber').values('subtype'))
```

### Find bills authored by senators in a specific congress
```groovy
g.V().hasLabel('Group')
  .has('type', 'chamber')
  .has('subtype', 'senate')
  .has('congress', 19)
  .in('MEMBER_OF')
  .as('person')
  .out('AUTHORED')
  .has('congress', 19)
  .project('author', 'bill_number', 'title')
    .by(select('person').values('last_name', 'first_name').fold())
    .by('bill_number')
    .by('title')
```

### Get bill authorship statistics
```groovy
// Count bills per author in 19th Congress
g.V().hasLabel('Congress')
  .has('congress_number', 19)
  .in('FILED_IN')
  .in('AUTHORED')
  .groupCount()
    .by(values('last_name', 'first_name').fold())
  .order(local).by(values, desc)
  .limit(local, 10)
```

### Find co-authored bills
```groovy
// Find bills with multiple authors
g.V().hasLabel('Document')
  .where(__.in('AUTHORED').count().is(gt(1)))
  .project('bill_number', 'title', 'authors')
    .by('bill_number')
    .by('title')
    .by(__.in('AUTHORED')
          .values('last_name', 'first_name')
          .fold())
```

## Data Import Process

The database is populated by `scripts/sync_to_janusgraph.py` which:

1. Reads TOML files from:
   - `data/congress/*.toml` - Congress entities
   - `data/group/chamber/*.toml` - Chamber (Senate/House) entities
   - `data/committee/*.toml` - Committee entities
   - `data/person/*.toml` - Person entities
   - `data/person/.senate-website-key-mapping.yml` - Mapping of Senate website author codes to person IDs
   - `data/person/.house-website-key-mapping.yml` - Mapping of House website author codes to person IDs
   - `data/document/hb/[congress]/*.toml` - House Bill documents (organized by congress number)
   - `data/document/hb/[congress]/.house-bill-number-mapping.yml` - Mapping of bill numbers to document IDs
   - `data/document/sb/[congress]/*.toml` - Senate Bill documents (organized by congress number)
   - `data/document/sb/[congress]/.senate-bill-number-mapping.yml` - Mapping of bill numbers to document IDs

2. Creates vertices with upsert operations (create if not exists, update if exists) using batch operations for performance

3. Establishes edges based on:
   - Chamber TOML files contain `congress` field → creates BELONGS_TO edges to Congress
   - Committee TOML files contain `congresses` array → creates BELONGS_TO edges to Congress
   - Person TOML files contain `memberships` array with chamber details → creates MEMBER_OF edges to appropriate Group vertices
   - Document TOML files contain:
     - `meta.congress` → creates FILED_IN edges to Congress
     - `meta.senate_website_author_codes` → creates AUTHORED edges from Person vertices (using Senate mapping file)
     - `meta.congress_website_author_codes` → creates AUTHORED edges from Person vertices (using House mapping file)

4. Creates indexes for optimized querying

### Performance Optimizations

The sync script uses several optimizations for faster data import with large datasets (150k+ House Bills):

- **Memory-efficient streaming**: Processes documents congress-by-congress using mapping files
- **Configurable batch size**: Default 500 documents per batch (configurable via `--batch-size`)
  - CI/CD environments: 500-1000 (conservative memory usage)
  - Local development: 1000-2000 (balanced)
  - High-end workstations: 2000-5000 (maximum speed)
- **Reduced network round trips**: Groups related operations together
- **Progress tracking**: Shows real-time progress per congress and bill type
- **Numerical congress ordering**: Processes congresses in correct order (8, 9, 10... not 10, 11, 12... 8, 9)

### Command Line Options

```bash
# Normal sync with default batch size (500)
python scripts/sync_to_janusgraph.py

# Sync with custom batch size for faster processing
python scripts/sync_to_janusgraph.py --batch-size 2000

# Clear database first (will prompt for confirmation)
python scripts/sync_to_janusgraph.py --clear

# Clear database and sync with high performance settings (for CI/CD)
python scripts/sync_to_janusgraph.py --clear --yes --batch-size 1000

# Get help and see all options
python scripts/sync_to_janusgraph.py --help
```

## Connection Configuration

The sync script requires the following environment variables:

```env
JANUSGRAPH_URI=ws://localhost:8182/gremlin
```

## Docker Compose Setup

You can run JanusGraph locally with Docker Compose:

```bash
# Start JanusGraph with ScyllaDB and Elasticsearch
docker-compose -f docker-compose.janusgraph.yml up -d

# Wait for services to be healthy (about 60 seconds)
docker-compose -f docker-compose.janusgraph.yml ps

# Run sync script
python scripts/sync_to_janusgraph.py

# Stop services
docker-compose -f docker-compose.janusgraph.yml down
```

The Docker Compose setup includes:
- **JanusGraph Server**: Graph database with Gremlin Server (port 8182)
- **ScyllaDB**: Cassandra-compatible storage backend (port 9042)
- **Elasticsearch**: Full-text search indexing (port 9200)

## Gremlin vs Cypher Comparison

For those familiar with Neo4j's Cypher, here's a comparison:

| Operation | Cypher (Neo4j) | Gremlin (JanusGraph) |
|-----------|----------------|----------------------|
| Find vertex | `MATCH (c:Congress {id: id})` | `g.V().hasLabel('Congress').has('id', id)` |
| Create vertex | `MERGE (c:Congress {id: id})` | `g.V().has('Congress', 'id', id).fold().coalesce(unfold(), addV('Congress').property('id', id))` |
| Create edge | `MATCH (a)-[:REL]->(b)` | `g.V(a).addE('REL').to(V(b))` |
| Traverse out | `MATCH (a)-[:REL]->(b)` | `g.V(a).out('REL')` |
| Traverse in | `MATCH (a)<-[:REL]-(b)` | `g.V(a).in('REL')` |
| Count | `RETURN count(n)` | `g.V().count()` |
| Filter | `WHERE n.prop = value` | `.has('prop', value)` |

## REST API Usage

External REST APIs can query this database using the Gremlin Python, Java, JavaScript, or other language drivers. The graph structure allows for:

- Efficient traversal of relationships
- Complex filtering across multiple entity types
- Aggregation queries for statistics
- Full-text search on indexed properties (via Elasticsearch)
- Clear separation between chambers (Senate/House)
- **Horizontal scalability** for large datasets

## Notes for API Development

1. **Connection Pooling:** Use connection pooling in production for better performance with Gremlin drivers

2. **Batch Operations:** Group related queries together to reduce network overhead

3. **Chamber Navigation:** To find which congress a person served in, you must traverse through the Group (chamber) vertex:
   - Person → MEMBER_OF → Group → BELONGS_TO → Congress

4. **Performance:** Use indexed properties in `.has()` steps when possible for optimal query performance

5. **Data Consistency:** The upsert operations ensure no duplicate vertices are created based on the `id` property

6. **Chamber Types:** Always filter Group vertices by `type: "chamber"` when looking for Senate/House chambers, as the Group label may be used for other entity types in the future

7. **Scalability:** JanusGraph scales horizontally - add more storage nodes as data grows

8. **Transactions:** For write operations, use transactions to ensure ACID compliance

## Monitoring and Maintenance

### Checking JanusGraph Status

```bash
# Check if JanusGraph is running
curl http://localhost:8182?gremlin=g.V().limit(1)

# Check vertex counts
curl -X POST http://localhost:8182 \
  -d '{"gremlin": "g.V().groupCount().by(label)"}'

# Check storage backend (ScyllaDB)
docker exec janusgraph-scylla cqlsh -e "SELECT * FROM system.local"
```

### Backup and Recovery

JanusGraph data is stored in ScyllaDB/Cassandra. Use standard Cassandra backup tools:

```bash
# Backup ScyllaDB data
docker exec janusgraph-scylla nodetool snapshot

# List snapshots
docker exec janusgraph-scylla nodetool listsnapshots
```

## Migration from Neo4j

If you're migrating from Neo4j:

1. Both databases can run in parallel during transition
2. Data structure remains the same (same TOML source files)
3. Query syntax changes from Cypher to Gremlin (see comparison table above)
4. Benefits: Better scalability, no licensing restrictions, industry-standard query language
