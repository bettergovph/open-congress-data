# GitHub Configuration

This directory contains GitHub-specific configurations for the open-congress-data repository.

## 📋 Issue Templates

Located in `ISSUE_TEMPLATE/`, these help users report issues with proper structure:

### 1. Data Quality Issue (`data-quality-issue.md`)
Use this for reporting:
- Duplicate entries
- Missing persons or entities
- Incorrect information
- Wrong chamber assignments
- Name spelling issues

### 2. Bug Report (`bug-report.md`)
Use this for:
- Script errors
- Sync process issues
- Technical problems

### 3. Feature Request (`feature-request.md`)
Use this for suggesting:
- New data fields
- New entity types
- Script improvements
- Documentation enhancements

## 🔄 Pull Request Template

The `pull_request_template.md` helps contributors submit well-structured PRs with:
- Clear description of changes
- Data verification sources
- Testing checklist
- Related issues linking

## 🏷️ Labels System

The `labels.yml` file defines all repository labels organized by category:

### Label Categories

#### Data Quality Labels (Orange/Yellow tones)
- `data-quality` - General data issues
- `needs-verification` - Requires source verification
- `duplicate-data` - Duplicate entries
- `missing-data` - Missing information
- `incorrect-data` - Wrong information

#### Entity Labels (Purple/Blue tones)
- `entity:person` - Person-related issues
- `entity:congress` - Congress-related issues
- `entity:committee` - Committee-related issues
- `entity:chamber` - Chamber-related issues

#### Priority Labels (Traffic light colors)
- `priority:high` - Urgent issues (red)
- `priority:medium` - Standard priority (orange)
- `priority:low` - Can wait (green)

#### Status Labels
- `verified` - Data has been verified (green)
- `in-progress` - Work in progress (blue)
- `blocked` - Blocked by dependencies (orange)
- `ready-for-review` - Ready for review (purple)

## 🤖 Automated Label Management

### Workflow: sync-labels.yml

This GitHub Actions workflow automatically manages repository labels.

#### How It Works

1. **Automatic Triggers:**
   - When `labels.yml` is modified
   - When the workflow file itself is updated
   - Manual trigger via Actions tab

2. **What It Does:**
   - Reads label definitions from `labels.yml`
   - Creates new labels that don't exist
   - Updates existing labels (color/description)
   - Deletes labels not in config (if configured)

3. **No Setup Required:**
   - Uses GitHub's built-in `GITHUB_TOKEN`
   - No personal access tokens needed
   - Automatically has correct permissions

#### Manual Trigger

To manually sync labels:

1. Go to the **Actions** tab in your repository
2. Select **"Sync Labels"** workflow
3. Click **"Run workflow"**
4. Select branch and click **"Run workflow"**

#### Configuration Options

In `sync-labels.yml`, you can modify:

```yaml
delete-other-labels: true  # Set to false to keep unlisted labels
```

⚠️ **Note:** When `delete-other-labels: true`, the workflow will remove any labels not defined in `labels.yml` to maintain a clean label system.

## 🛠️ Alternative: Manual Label Creation

### GitHub Web Interface

If you prefer to create labels manually:

1. Go to **Settings** → **Labels** in your repository
2. Click **"New label"**
3. Create each label from `labels.yml` manually

## 📊 Label Usage Guidelines

### When Creating Issues

1. **Always apply:**
   - One issue type label (`bug`, `enhancement`, etc.)
   - Relevant entity label if applicable
   - `data-quality` for data issues

2. **Add when known:**
   - Priority label
   - Source label for data issues
   - `needs-verification` if sources needed

3. **Maintainers will add:**
   - Status labels (`in-progress`, `blocked`, etc.)
   - `verified` once confirmed
   - Contribution labels (`good-first-issue`, `help-wanted`)

### Example Label Combinations

**Data Quality Issue:**
- `data-quality`
- `duplicate-data`
- `entity:person`
- `needs-verification`
- `priority:medium`

**Bug Report:**
- `bug`
- `priority:high`

**Feature Request:**
- `enhancement`
- `entity:chamber`
- `priority:low`

## 🔄 Workflows Overview

### 1. sync-labels.yml
- **Purpose:** Automatically sync GitHub labels
- **Triggers:** On label config change or manual
- **Permissions:** Uses built-in `GITHUB_TOKEN` with `issues: write` and `pull-requests: write`
- **No setup required:** Works out of the box

### 2. sync-to-neo4j.yml
- **Purpose:** Sync data to Neo4j database
- **Triggers:** Push to main branch or manual
- **Requires:** Neo4j credentials in repository secrets

## 📚 Additional Resources

- [Contributing Guide](../CONTRIBUTING.md) - How to contribute
- [Development Guide](../DEVELOPMENT.md) - Setup instructions
- [Database Documentation](../DATABASE.md) - Neo4j schema
- [GitHub Labels Best Practices](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels)

## ❓ Need Help?

If you have questions:
1. Check existing [Issues](https://github.com/bettergovph/open-congress-data/issues)
2. Start a [Discussion](https://github.com/bettergovph/open-congress-data/discussions)
3. Review the documentation above
4. Create an issue using the appropriate template

## 🚀 Quick Start for Maintainers

1. **First Time Setup:**
   - Push these changes to your repository
   - Go to Actions → Sync Labels → Run workflow
   - All labels will be created automatically

2. **Adding New Labels:**
   - Edit `.github/labels.yml`
   - Commit and push
   - Labels sync automatically via GitHub Actions

3. **Modifying Labels:**
   - Update in `labels.yml`
   - Changes apply automatically on push

4. **Removing Labels:**
   - Delete from `labels.yml`
   - Push changes
   - Workflow removes them automatically (when `delete-other-labels: true`)

---

*This configuration helps maintain consistent issue tracking and contribution workflows for the open-congress-data project.*