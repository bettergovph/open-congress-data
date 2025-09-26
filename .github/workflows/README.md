# GitHub Actions Configuration

## Neo4j Sync Workflow

The `sync-to-neo4j.yml` workflow automatically syncs data to your Neo4j database whenever changes are pushed to the main branch.

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

### Workflow Triggers

The workflow runs automatically when:
- Code is pushed to the `main` branch
- Manually triggered via GitHub Actions UI (workflow_dispatch)

### What the Workflow Does

1. Checks out the latest code
2. Sets up Python 3.12 environment
3. Installs required dependencies from `requirements.txt`
4. Runs `python3 scripts/sync_to_neo4j.py --clear` to:
   - Clear existing Congress, Committee, and Person nodes
   - Sync fresh data from TOML files to Neo4j
   - Create database indexes for optimal query performance

### Manual Trigger

You can manually run the workflow:
1. Go to Actions tab in your repository
2. Select "Sync to Neo4j" workflow
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