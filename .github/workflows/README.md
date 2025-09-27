# GitHub Actions Configuration

## Neo4j Sync Workflows

There are two workflows for syncing data to Neo4j:

### 1. Incremental Sync (`sync-to-neo4j-incremental.yml`)
- **Triggers**: Manual trigger only via GitHub Actions UI
- **Purpose**: Fast incremental updates without downtime
- **Behavior**: Updates/adds new data using MERGE operations (no clearing)

### 2. Full Sync with Clear (`sync-to-neo4j-full.yml`)
- **Triggers**: Manual trigger only via GitHub Actions UI
- **Purpose**: Complete database rebuild when needed
- **Behavior**: Clears all existing data and rebuilds from scratch

### Required GitHub Secrets

To enable the Neo4j sync workflow, you need to configure the following secrets in your GitHub repository:

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret" and add these three secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `NEO4J_URI` | Neo4j database connection URI | `bolt://localhost:7687` or `neo4j+s://xxxxx.databases.neo4j.io` |
| `NEO4J_USERNAME` | Neo4j database username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j database password | Your secure password |

### When to Use Each Workflow

**Incremental Sync**:
- Regular updates when adding/modifying people, committees, or congress data
- Quick updates with no downtime
- Preserves any manually added data in Neo4j
- Run after pushing changes to main branch

**Full Sync**:
- After major structural changes to the data model
- When you need to remove deleted entities from the database
- To ensure complete data consistency
- When troubleshooting data issues

### What Each Workflow Does

**Incremental Sync**:
1. Checks out the latest code
2. Sets up Python 3.12 environment
3. Installs required dependencies from `requirements.txt`
4. Runs `python3 scripts/sync_to_neo4j.py` to:
   - Update existing nodes with MERGE operations
   - Add new nodes from TOML files
   - Create/verify database indexes

**Full Sync**:
1. Same setup as incremental
2. Runs `python3 scripts/sync_to_neo4j.py --clear --yes` to:
   - Clear ALL existing Congress, Committee, and Person nodes
   - Rebuild database from scratch with fresh data
   - Recreate all indexes

### Manual Trigger

To run either workflow:
1. Go to Actions tab in your repository
2. Select the desired workflow:
   - "Incremental Sync to Neo4j" for updates without clearing
   - "Full Sync to Neo4j (with Clear)" for complete rebuild
3. Click "Run workflow"
4. Select the branch and click "Run workflow"

### Monitoring

- Check the Actions tab to monitor workflow runs
- Each run shows detailed logs of the sync process
- Failed syncs will be marked with a ❌ and prevent the merge

### Troubleshooting

If the workflow fails:
1. Check that all three secrets are properly configured
2. Verify your Neo4j instance is accessible from GitHub Actions
3. Ensure the Neo4j credentials have write permissions
4. Review the workflow logs for specific error messages

For Neo4j cloud instances (Aura), make sure to use the `neo4j+s://` protocol in your URI.