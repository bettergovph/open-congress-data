# Development Guide

This guide will help you set up and run the Neo4j sync script to import
Philippine Congress data into a Neo4j graph database.

## Prerequisites

### Python Installation

Ensure you have Python 3.8 or higher installed:

```bash
python3 --version
```

If Python is not installed, download it from
[python.org](https://www.python.org/downloads/) or use a package manager:

- **macOS**: `brew install python3`
- **Ubuntu/Debian**: `sudo apt-get install python3 python3-pip`
- **Windows**: Download the installer from python.org

## Setting Up the Development Environment

### 1. Create a Python Virtual Environment

Virtual environments help isolate project dependencies. From the project root
directory:

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 2. Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

This will install:

- `neo4j`: Official Neo4j Python driver
- `python-dotenv`: For loading environment variables
- `tomli`: For parsing TOML files

## Setting Up Neo4j

### Option 1: Neo4j AuraDB (Recommended - Free Tier Available)

1. **Create a Free Account**
   - Go to [Neo4j AuraDB](https://neo4j.com/cloud/aura-free/)
   - Click "Start Free"
   - Sign up with your email or Google/GitHub account

2. **Create a Database**
   - Choose "Create a database"
   - Select "AuraDB Free" tier
   - Choose your region (pick the closest to you)
   - Click "Create Database"

3. **Save Your Credentials**
   - **IMPORTANT**: Save the generated password immediately (you won't see it
     again!)
   - Note down the Connection URI (format: `neo4j+s://xxxxx.databases.neo4j.io`)
   - The default username is `neo4j`

### Option 2: Local Neo4j Installation

1. **Download Neo4j Desktop**
   - Go to [Neo4j Desktop](https://neo4j.com/download/)
   - Download and install Neo4j Desktop

2. **Create a Local Database**
   - Open Neo4j Desktop
   - Create a new project
   - Add a local DBMS
   - Set a password for the `neo4j` user
   - Start the database

3. **Get Connection Details**
   - Default URI: `neo4j://localhost:7687` or `bolt://localhost:7687`
   - Username: `neo4j`
   - Password: (the one you set)

## Environment Configuration

1. **Copy the Environment Template**

```bash
cp .env.example .env
```

2. **Edit the `.env` File**

Open `.env` in your text editor and add your Neo4j credentials:

```env
# For Neo4j AuraDB:
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password-here

# For Local Neo4j:
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password-here
```

## Running the Sync Script

### Basic Usage

With your virtual environment activated:

```bash
python scripts/sync_to_neo4j.py
```

This will:

1. Connect to your Neo4j database
2. Create indexes for better performance
3. Sync all Congress data first
4. Sync Committee data with relationships to Congresses
5. Sync Person data with relationships to Congresses
6. Display statistics of imported data

### Clear and Resync

To clear only Congress, Committee, and Person nodes before syncing:

```bash
python scripts/sync_to_neo4j.py --clear
```

**Note**: This will only delete Congress, Committee, and Person nodes and their
relationships. Other data in the database will be preserved, making it safe for
shared databases.

The script will:

1. Show which node types will be deleted (Congress, Committee, Person)
2. Count how many nodes will be affected
3. Ask for confirmation before proceeding
4. Only delete the specified node types and their relationships

## Verifying the Data

### Using Neo4j Browser

1. **Access Neo4j Browser**
   - **AuraDB**: Click "Open" button in your AuraDB console
   - **Local**: Open http://localhost:7474 in your browser

2. **Sample Queries**

```cypher
// Count all nodes
MATCH (n) RETURN count(n);

// View all Congresses
MATCH (c:Congress)
RETURN c.name, c.congress_number, c.year_range
ORDER BY c.congress_number;

// Find all committees in the 14th Congress
MATCH (com:Committee)-[:BELONGS_TO]->(con:Congress {congress_number: 14})
RETURN com.name, com.type;

// Find all people who served in the 19th Congress
MATCH (p:Person)-[:SERVED_IN]->(c:Congress {congress_number: 19})
RETURN p.full_name, p.senate_website_keys
ORDER BY p.last_name;

// Find a person by a specific website key (searching in array)
MATCH (p:Person)
WHERE "ZMIGU" IN p.senate_website_keys
RETURN p.full_name, p.senate_website_keys;

// Find a committee by a specific website key
MATCH (c:Committee)
WHERE "ABSVO" IN c.senate_website_keys
RETURN c.name, c.type;

// Find people who served in multiple congresses
MATCH (p:Person)-[:SERVED_IN]->(c:Congress)
WITH p, count(c) as congress_count
WHERE congress_count > 1
RETURN p.full_name, congress_count, p.congresses
ORDER BY congress_count DESC;

// View the graph structure (limit to prevent overload)
MATCH (n)-[r]-(m)
RETURN n, r, m
LIMIT 100;
```

### Expected Data Structure

The script creates the following graph structure:

**Nodes:**

- `Congress`: Represents each congress with properties like name, number, dates
- `Committee`: Senate committees with their names and types
- `Person`: Senators and officials with names and other details

**Relationships:**

- `(Committee)-[:BELONGS_TO]->(Congress)`: Committee active in a congress
- `(Person)-[:SERVED_IN]->(Congress)`: Person served during a congress

## Troubleshooting

### Common Issues

1. **Connection Refused Error**
   - Verify your Neo4j database is running
   - Check the URI in your `.env` file
   - For AuraDB, ensure you're using `neo4j+s://` (with SSL)
   - For local, try both `neo4j://` and `bolt://`

2. **Authentication Failed**
   - Double-check username and password in `.env`
   - Default username is usually `neo4j`
   - For AuraDB, ensure you saved the auto-generated password

3. **Module Not Found Error**
   - Ensure your virtual environment is activated
   - Run `pip install -r requirements.txt` again

4. **TOML Parse Error**
   - Check if TOML files are properly formatted
   - Ensure no syntax errors in the data files

5. **Memory Issues with Large Datasets**
   - The script processes files one at a time to minimize memory usage
   - If issues persist, consider increasing Neo4j heap memory settings

### Getting Help

- Neo4j Documentation: https://neo4j.com/docs/
- Neo4j Python Driver: https://neo4j.com/docs/python-manual/current/
- Cypher Query Language: https://neo4j.com/docs/cypher-manual/current/

## Development Tips

### Modifying the Script

The script is modular and can be extended:

- Add new node properties: Update the relevant `sync_*` method
- Add new relationship types: Create new relationship queries
- Add validation: Implement data validation before syncing

### Performance Optimization

The script includes several optimizations:

- Batch processing of files
- Index creation before data import
- Use of `MERGE` to prevent duplicates
- Minimal memory footprint

For very large datasets, consider:

- Using `apoc.periodic.iterate` for batch processing
- Implementing parallel processing for file reading
- Using Neo4j's import tools for initial bulk loads
