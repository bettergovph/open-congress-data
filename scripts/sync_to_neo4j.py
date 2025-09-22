#!/usr/bin/env python3
"""
Sync Philippine Congress data from TOML files to Neo4j database.

This script reads TOML files containing congress, committee, and person data
and syncs them to a Neo4j database with appropriate relationships.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict
import tomli
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Neo4jSyncer:
    """Handle syncing data to Neo4j database."""

    def __init__(self, uri: str, username: str, password: str):
        """Initialize Neo4j connection."""
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close the Neo4j driver."""
        if self.driver:
            self.driver.close()

    def clear_database(self):
        """Clear specific node types and their relationships from the database."""
        # Define which node labels to clear - easy to update this list
        node_labels_to_clear = ["Congress", "Committee", "Person"]

        with self.driver.session() as session:
            try:
                # Count nodes that will be deleted
                label_conditions = " OR ".join(
                    [f"n:{label}" for label in node_labels_to_clear]
                )
                count_query = (
                    f"MATCH (n) WHERE {label_conditions} RETURN count(n) as count"
                )
                result = session.run(count_query)
                node_count = result.single()["count"]

                if node_count > 0:
                    # Show which types will be deleted
                    logger.info(
                        f"Will delete nodes with labels: {', '.join(node_labels_to_clear)}"
                    )
                    response = input(
                        f"This will delete {node_count} nodes and their relationships. Continue? (yes/no): "
                    )
                    if response.lower() == "yes":
                        # Delete only specific node types and their relationships
                        delete_query = (
                            f"MATCH (n) WHERE {label_conditions} DETACH DELETE n"
                        )
                        session.run(delete_query)
                        logger.info(
                            f"Cleared {node_count} nodes of types: {', '.join(node_labels_to_clear)}"
                        )
                    else:
                        logger.info("Clear operation cancelled")
                else:
                    logger.info(
                        f"No nodes found with labels: {', '.join(node_labels_to_clear)}"
                    )
            except Neo4jError as e:
                logger.error(f"Failed to clear database: {e}")
                raise

    def sync_congresses(self, congresses_dir: Path) -> Dict[int, str]:
        """Sync congress data to Neo4j and return congress number to ID mapping."""
        congress_mapping = {}

        with self.driver.session() as session:
            congress_files = sorted(congresses_dir.glob("*.toml"))
            logger.info(f"Found {len(congress_files)} congress files")

            for idx, file_path in enumerate(congress_files, 1):
                try:
                    with open(file_path, "rb") as f:
                        data = tomli.load(f)

                    congress_mapping[data["congress_number"]] = data["id"]

                    # Build SET clause dynamically to handle optional fields
                    set_clauses = []
                    params = {"id": data["id"]}

                    # Add all available fields
                    for field in data.keys():
                        if field != "id":
                            set_clauses.append(f"c.{field} = ${field}")
                            params[field] = data[field]

                    query = f"""
                    MERGE (c:Congress {{id: $id}})
                    SET {', '.join(set_clauses)}
                    """

                    session.run(query, **params)
                    logger.info(
                        f"[{idx}/{len(congress_files)}] Synced congress: {data['name']}"
                    )

                except Exception as e:
                    logger.error(f"Failed to sync {file_path}: {e}")

            logger.info(f"Successfully synced {len(congress_mapping)} congresses")

        return congress_mapping

    def sync_committees(self, committees_dir: Path, congress_mapping: Dict[int, str]):
        """Sync committee data to Neo4j with relationships to congresses."""
        # Get file list first
        committee_files = list(committees_dir.glob("*.toml"))
        total_files = len(committee_files)
        logger.info(f"Found {total_files} committee files")

        # Process in batches to avoid keeping everything in memory
        batch_size = 10

        with self.driver.session() as session:
            for idx, file_path in enumerate(sorted(committee_files), 1):
                try:
                    # Log which file we're processing
                    if idx % 5 == 1 or idx == 1:
                        logger.info(
                            f"Processing committee {idx}/{total_files}: {file_path.name}"
                        )

                    with open(file_path, "rb") as f:
                        data = tomli.load(f)

                    # Add all fields from TOML except 'congresses' (used only for relationships)
                    # This includes senate_website_keys array automatically
                    params = {k: v for k, v in data.items() if k != "congresses"}

                    # Build SET clause dynamically for all fields
                    set_clauses = [
                        f"c.{field} = ${field}"
                        for field in params.keys()
                        if field != "id"
                    ]

                    # Create committee node with all properties
                    query = f"""
                    MERGE (c:Committee {{id: $id}})
                    SET {', '.join(set_clauses)}
                    """

                    session.run(query, **params)

                    # Create relationships to congresses
                    for congress_num in data.get("congresses", []):
                        if congress_num in congress_mapping:
                            rel_query = """
                            MATCH (com:Committee {id: $committee_id})
                            MATCH (con:Congress {id: $congress_id})
                            MERGE (com)-[:BELONGS_TO]->(con)
                            """
                            session.run(
                                rel_query,
                                committee_id=data["id"],
                                congress_id=congress_mapping[congress_num],
                            )

                    # Clear data from memory after processing
                    del data

                    if idx % batch_size == 0:
                        logger.info(f"Progress: {idx}/{total_files} committees synced")
                        # Force a commit every batch
                        session.commit()

                except Exception as e:
                    logger.error(f"Failed to sync {file_path.name}: {e}")
                    continue

            logger.info(f"Successfully synced committees")

    def sync_people(self, people_dir: Path, congress_mapping: Dict[int, str]):
        """Sync person data to Neo4j with relationships to congresses."""
        # Get file list first
        people_files = list(people_dir.glob("*.toml"))
        total_files = len(people_files)
        logger.info(f"Found {total_files} people files")

        # Process in batches to avoid keeping everything in memory
        batch_size = 10

        with self.driver.session() as session:
            for idx, file_path in enumerate(sorted(people_files), 1):
                try:
                    # Log which file we're processing
                    if idx % 5 == 1 or idx == 1:
                        logger.info(
                            f"Processing person {idx}/{total_files}: {file_path.name}"
                        )

                    with open(file_path, "rb") as f:
                        data = tomli.load(f)

                    # Add all fields from TOML except 'congresses' (used only for relationships)
                    # This includes senate_website_keys array, aliases, and all other fields automatically
                    params = {k: v for k, v in data.items() if k != "congresses"}

                    # Build SET clause dynamically for all fields
                    set_clauses = [
                        f"p.{field} = ${field}"
                        for field in params.keys()
                        if field != "id"
                    ]

                    # Create person node with all properties
                    query = f"""
                    MERGE (p:Person {{id: $id}})
                    SET {', '.join(set_clauses)}
                    """

                    session.run(query, **params)

                    # Create relationships to congresses
                    for congress_num in data.get("congresses", []):
                        if congress_num in congress_mapping:
                            rel_query = """
                            MATCH (p:Person {id: $person_id})
                            MATCH (c:Congress {id: $congress_id})
                            MERGE (p)-[:SERVED_IN]->(c)
                            """
                            session.run(
                                rel_query,
                                person_id=data["id"],
                                congress_id=congress_mapping[congress_num],
                            )

                    # Clear data from memory after processing
                    del data

                    if idx % batch_size == 0:
                        logger.info(f"Progress: {idx}/{total_files} people synced")
                        # Force a commit every batch
                        session.commit()

                except Exception as e:
                    logger.error(f"Failed to sync {file_path.name}: {e}")
                    continue

            logger.info(f"Successfully synced people")

    def create_indexes(self):
        """Create indexes for better query performance."""
        with self.driver.session() as session:
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (c:Congress) ON (c.id)",
                "CREATE INDEX IF NOT EXISTS FOR (c:Congress) ON (c.congress_number)",
                "CREATE INDEX IF NOT EXISTS FOR (com:Committee) ON (com.id)",
                "CREATE INDEX IF NOT EXISTS FOR (com:Committee) ON (com.name)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.id)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.full_name)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.last_name)",
            ]
            # Note: We don't create indexes on senate_website_keys arrays
            # To search for a specific key in the array, use:
            # MATCH (p:Person) WHERE "ABENI" IN p.senate_website_keys

            for index_query in indexes:
                try:
                    session.run(index_query)
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")

            logger.info("Database indexes created/verified")

    def get_statistics(self):
        """Get statistics about the synced data."""
        with self.driver.session() as session:
            stats = {}

            # Count nodes
            for label in ["Congress", "Committee", "Person"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                stats[label] = result.single()["count"]

            # Count relationships
            for rel_type in ["BELONGS_TO", "SERVED_IN"]:
                result = session.run(
                    f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                )
                stats[rel_type] = result.single()["count"]

            return stats


def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()

    # Get configuration
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    if not all([neo4j_uri, neo4j_username, neo4j_password]):
        logger.error(
            "Missing required environment variables. Please check your .env file."
        )
        logger.error("Required: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")
        sys.exit(1)

    # Get project root directory
    project_root = Path(__file__).parent.parent
    congresses_dir = project_root / "data" / "congress"
    committees_dir = project_root / "data" / "committee"
    people_dir = project_root / "data" / "person"

    # Verify directories exist
    for dir_path in [congresses_dir, committees_dir, people_dir]:
        if not dir_path.exists():
            logger.error(f"Directory not found: {dir_path}")
            sys.exit(1)

    # Initialize syncer
    syncer = None
    try:
        syncer = Neo4jSyncer(neo4j_uri, neo4j_username, neo4j_password)

        # Optional: Clear database
        if len(sys.argv) > 1 and sys.argv[1] == "--clear":
            syncer.clear_database()

        # Create indexes first for better performance
        logger.info("Creating database indexes...")
        syncer.create_indexes()

        # Sync data in order
        logger.info("Starting data sync...")

        # 1. Sync Congresses first (they're referenced by committees and people)
        logger.info("Syncing congresses...")
        congress_mapping = syncer.sync_congresses(congresses_dir)

        # 2. Sync Committees
        logger.info("Syncing committees...")
        syncer.sync_committees(committees_dir, congress_mapping)

        # 3. Sync People
        logger.info("Syncing people...")
        syncer.sync_people(people_dir, congress_mapping)

        # Display statistics
        stats = syncer.get_statistics()
        logger.info("\n=== Sync Complete ===")
        logger.info(f"Congresses: {stats['Congress']}")
        logger.info(f"Committees: {stats['Committee']}")
        logger.info(f"People: {stats['Person']}")
        logger.info(f"Committee-Congress relationships: {stats['BELONGS_TO']}")
        logger.info(f"Person-Congress relationships: {stats['SERVED_IN']}")

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)
    finally:
        if syncer:
            syncer.close()


if __name__ == "__main__":
    main()
