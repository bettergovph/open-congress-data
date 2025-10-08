# JanusGraph Implementation

This directory contains the JanusGraph implementation for the Philippine Congress data, providing a scalable, distributed graph database alternative to Neo4j.

## Why JanusGraph?

- **Horizontal Scalability**: Distributed architecture supports massive datasets
- **Multiple Storage Backends**: ScyllaDB, Cassandra, HBase, or BerkeleyDB
- **Open Source**: No licensing restrictions
- **Industry Standard**: TinkerPop/Gremlin query language
- **Full-text Search**: Elasticsearch integration for advanced text queries

## Files in This Directory

- **`docker-compose.yml`** - Docker Compose setup with JanusGraph, ScyllaDB, and Elasticsearch
- **`DATABASE.md`** - Complete schema documentation with Gremlin query examples

## Related Files

- **`../scripts/sync_to_janusgraph.py`** - Python script to sync data from TOML files to JanusGraph
- **`../requirements.txt`** - Python dependencies (includes gremlinpython and supporting libraries)
- **`../.github/workflows/sync-to-janusgraph.yml`** - GitHub Actions workflow for automated syncing

## Quick Start

### 1. Start JanusGraph with Docker Compose

```bash
cd janusgraph
docker-compose up -d
```

This will start:
- JanusGraph server on port 8182 (Gremlin WebSocket)
- ScyllaDB on port 9042 (Cassandra-compatible storage)
- Elasticsearch on port 9200 (full-text search)

Wait about 60 seconds for all services to be healthy:

```bash
docker-compose ps
```

### 2. Install Python Dependencies

From the project root:

```bash
pip install -r requirements.txt
```

This installs all dependencies including `gremlinpython` for JanusGraph and `neo4j` for Neo4j.

### 3. Configure Connection

Create a `.env` file in the project root (or set environment variable):

```env
JANUSGRAPH_URI=ws://localhost:8182/gremlin
```

If not set, defaults to `ws://localhost:8182/gremlin`.

### 4. Run the Sync Script

From the project root:

```bash
# Normal sync with default settings (batch_size=500)
python scripts/sync_to_janusgraph.py

# Clear database first (with confirmation)
python scripts/sync_to_janusgraph.py --clear

# Clear database without confirmation (for CI/CD)
python scripts/sync_to_janusgraph.py --clear --yes

# Use larger batch size for faster syncing
python scripts/sync_to_janusgraph.py --batch-size 2000

# Combined: clear and sync with high performance settings
python scripts/sync_to_janusgraph.py --clear --yes --batch-size 1000
```

### 5. Verify the Sync

Check the statistics at the end of the sync output:

```
=== Sync Complete ===
Total sync time: 120.5 seconds
Congresses: 13
Chambers (Group): 26
Committees: 45
People: 850
Documents: 150000
BELONGS_TO edges: 71
MEMBER_OF edges: 1200
AUTHORED edges: 200000
FILED_IN edges: 150000
```

## Command-Line Options

```bash
python scripts/sync_to_janusgraph.py --help
```

**Available options:**
- `--clear` - Clear database before syncing (prompts for confirmation)
- `--yes` / `-y` - Skip confirmation prompts (useful for CI/CD)
- `--batch-size N` - Number of documents to process per batch (default: 500)

**Batch Size Recommendations:**
- CI/CD (GitHub Actions): 500-1000 (conservative)
- Standard laptop (8-16GB RAM): 1000-2000 (balanced)
- High-end workstation (32GB+ RAM): 2000-5000 (fast)

## Querying the Database

### Using Gremlin Console (via Docker)

```bash
# Connect to Gremlin console
docker exec -it janusgraph-server bin/gremlin.sh

# Once in the console
gremlin> :remote connect tinkerpop.server conf/remote.yaml
gremlin> :remote console

# Example queries
gremlin> g.V().hasLabel('Congress').valueMap()
gremlin> g.V().hasLabel('Person').has('last_name', 'Aquino').valueMap()
gremlin> g.V().hasLabel('Document').has('congress', 19).count()
```

### Using Python (gremlinpython)

```python
from gremlin_python.driver import client

# Connect to JanusGraph
gremlin_client = client.Client('ws://localhost:8182/gremlin', 'g')

# Find all congresses
result = gremlin_client.submit("g.V().hasLabel('Congress').valueMap()").all().result()
print(result)

# Find person by last name
result = gremlin_client.submit(
    "g.V().hasLabel('Person').has('last_name', name).valueMap()",
    {"name": "Aquino"}
).all().result()
print(result)

# Close connection
gremlin_client.close()
```

## Common Gremlin Queries

See [DATABASE.md](DATABASE.md) for a comprehensive list of query examples, including:

- Finding senators/representatives by congress
- Tracking political careers across congresses
- Finding bills by author
- Counting bills by congress
- Finding co-authored bills
- And many more...

## Monitoring and Maintenance

### Check Service Health

```bash
# Check all services
docker-compose ps

# Check JanusGraph logs
docker-compose logs -f janusgraph

# Check ScyllaDB status
docker exec janusgraph-scylla nodetool status

# Check Elasticsearch status
curl http://localhost:9200/_cluster/health?pretty
```

### Database Statistics

```bash
# Get vertex counts by label
curl -X POST http://localhost:8182 \
  -d '{"gremlin": "g.V().groupCount().by(label)"}'

# Get edge counts by label
curl -X POST http://localhost:8182 \
  -d '{"gremlin": "g.E().groupCount().by(label)"}'
```

### Backup and Recovery

JanusGraph data is stored in ScyllaDB. Use standard Cassandra backup tools:

```bash
# Create snapshot
docker exec janusgraph-scylla nodetool snapshot

# List snapshots
docker exec janusgraph-scylla nodetool listsnapshots

# Clear snapshots
docker exec janusgraph-scylla nodetool clearsnapshot
```

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v
```

## GitHub Actions Integration

The workflow is already configured at `.github/workflows/sync-to-janusgraph.yml`.

To enable automated syncing on push to main:

1. Add the `JANUSGRAPH_URI` secret to your GitHub repository:
   - Go to repository Settings → Secrets and variables → Actions
   - Add new secret: `JANUSGRAPH_URI` = your JanusGraph connection URI

The workflow will automatically sync data whenever changes are pushed to the main branch.

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Full reset (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Connection refused errors

- Wait 60-90 seconds after starting for all services to be healthy
- Check if all containers are running: `docker-compose ps`
- Verify ports are not already in use: `lsof -i :8182`, `lsof -i :9042`, `lsof -i :9200`

### Out of memory errors

- Reduce batch size: `python scripts/sync_to_janusgraph.py --batch-size 250`
- Increase Docker memory limit in Docker Desktop settings
- Check service memory: `docker stats`

### Slow sync performance

- Increase batch size if you have enough RAM: `python scripts/sync_to_janusgraph.py --batch-size 2000`
- Check if Elasticsearch is running (indexes speed up queries)
- Monitor resource usage: `docker stats`

## Schema Documentation

For detailed information about the database schema, vertex/edge types, and comprehensive Gremlin query examples, see:

**[DATABASE.md](DATABASE.md)**

Includes:
- Complete vertex (node) and edge (relationship) documentation
- Property definitions and data types
- Gremlin query patterns for common operations
- Cypher vs Gremlin comparison table
- Index configuration
- Performance optimization tips

## Migration from Neo4j

If you're migrating from Neo4j:

1. **Data structure is identical** - Both use the same TOML source files from `../data/`
2. **Run in parallel** - You can run both Neo4j and JanusGraph simultaneously during transition
3. **Query language changes** - Cypher → Gremlin (see DATABASE.md for comparison)
4. **Benefits**: Better scalability, no licensing issues, industry-standard TinkerPop/Gremlin

## Support

For issues or questions:
- Review the [DATABASE.md](DATABASE.md) documentation
- Check the main repository README
- Open an issue on GitHub
