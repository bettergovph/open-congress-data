# GitHub Actions Configuration

## Neo4j Sync Workflow

There is one workflow for syncing data to Neo4j:

### Full Sync (`sync-to-neo4j.yml`)
- **Triggers**: Push to main branch or manual trigger via GitHub Actions UI
- **Purpose**: Complete database rebuild with latest data
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

### When the Workflow Runs

**Automatic Triggers**:
- On every push to the main branch
- Ensures database always reflects the latest data

**Manual Trigger**:
- Can be triggered manually from GitHub Actions UI
- Useful for testing or immediate updates

### What the Workflow Does

1. Checks out the latest code
2. Sets up Python 3.12 environment
3. Installs required dependencies from `requirements.txt`
4. Runs `python3 scripts/sync_to_neo4j.py --clear --yes` to:
   - Clear ALL existing Congress, Committee, Person, and Group nodes
   - Rebuild database from scratch with fresh data
   - Recreate all indexes
   - Create proper relationships between entities

### Manual Trigger

To run the workflow manually:
1. Go to Actions tab in your repository
2. Select "Full Sync to Neo4j (with Clear)"
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