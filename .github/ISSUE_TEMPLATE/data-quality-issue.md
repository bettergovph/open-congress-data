---
name: Data Quality Issue
about: Report incorrect, duplicate, or missing data in the dataset
title: '[DATA] '
labels: 'data-quality, needs-verification'
assignees: ''
---

## Issue Type
<!-- Check the type of data issue you're reporting -->

- [ ] Duplicate entry
- [ ] Missing person/entity
- [ ] Incorrect information
- [ ] Wrong chamber assignment
- [ ] Incorrect congress membership
- [ ] Name spelling/format issue
- [ ] Missing aliases
- [ ] Other (please describe)

## Affected Data
<!-- Specify which entity type and files are affected -->

**Entity Type:**
- [ ] Person
- [ ] Congress
- [ ] Committee
- [ ] Chamber (Group)

**File(s) affected (if known):**
<!-- Example: data/person/01K5S1TKQYXMDG8MDDP8E0XX0K.toml -->
```
[paste file path(s) here]
```

## Description
<!-- Provide a clear description of the data issue -->

### Current (Incorrect) Data
<!-- What is currently in the dataset that's wrong? -->
```toml
# Paste the incorrect TOML data here
```

### Expected (Correct) Data
<!-- What should the correct data be? -->
```toml
# Paste what the correct TOML data should look like
```

## Evidence/Sources
<!-- Provide sources to verify the correct information -->

- [ ] Senate website: [link]
- [ ] House of Representatives website: [link]
- [ ] Official government document: [link]
- [ ] News article: [link]
- [ ] Other source: [describe and link]

## Additional Context
<!-- Add any other context about the problem -->

### For Duplicate Issues
- **Person/Entity 1:** [name and file path]
- **Person/Entity 2:** [name and file path]
- **Why they're the same:** [explanation]

### For Missing Person/Entity
- **Name:**
- **Position:** (Senator/Representative)
- **Congress(es) served:**
- **Chamber:** (Senate/House)
- **Source confirming their service:**

### For Incorrect Chamber/Congress Assignment
- **Person name:**
- **Current assignment:** (e.g., "Senate in 15th Congress")
- **Correct assignment:** (e.g., "House in 15th Congress")
- **Source:**

## Suggested Fix
<!-- Optional: If you know how to fix it, describe the solution -->

```toml
# If you have a suggested TOML configuration, paste it here
```

## Checklist
<!-- Please check all that apply -->

- [ ] I've searched existing issues to avoid duplicates
- [ ] I've provided sources to verify the correct information
- [ ] I've clearly identified which files are affected (if known)
- [ ] I've provided enough detail for someone to verify and fix the issue

---
<!--
Thank you for helping improve the data quality of this project!
Your contribution helps ensure accurate representation of Philippine Congress data.
-->