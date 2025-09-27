#!/usr/bin/env python3
"""
Optimized sync script for Philippine Congress data to Neo4j database.

This version uses batch operations and transactions for much faster syncing.
Performance improvements:
- Batch UNWIND operations for multiple nodes at once
- Single transaction per batch instead of per node
- Reduced network round trips

Usage:
    python sync_to_neo4j_optimized.py                # Sync data without clearing
    python sync_to_neo4j_optimized.py --clear        # Clear database first (will prompt for confirmation)
    python sync_to_neo4j_optimized.py --clear --yes  # Clear database first (skip confirmation - for CI/CD)
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, List
import tomlkit
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Neo4jSyncerOptimized:
    """Optimized handler for syncing data to Neo4j database using batch operations."""

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

    def clear_database(self, skip_confirmation=False):
        """Clear specific node types and their relationships from the database."""
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
                    logger.info(
                        f"Will delete nodes with labels: {', '.join(node_labels_to_clear)}"
                    )

                    if skip_confirmation:
                        logger.info(f"Auto-confirming deletion of {node_count} nodes (--yes flag provided)")
                        response = "yes"
                    else:
                        response = input(
                            f"This will delete {node_count} nodes and their relationships. Continue? (yes/no): "
                        )

                    if response.lower() == "yes":
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

    def sync_congresses_batch(self, congresses_dir: Path) -> Dict[int, str]:
        """Sync congress data to Neo4j using batch operations."""
        congress_mapping = {}
        congress_batch = []

        congress_files = sorted(congresses_dir.glob("*.toml"))
        logger.info(f"Found {len(congress_files)} congress files")

        # Load all congress data
        for file_path in congress_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = tomlkit.load(f)
                    congress_mapping[data["congress_number"]] = data["id"]
                    congress_batch.append(dict(data))
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

        # Batch insert all congresses in a single transaction
        if congress_batch:
            with self.driver.session() as session:
                query = """
                UNWIND $batch AS congress
                MERGE (c:Congress {id: congress.id})
                SET c = congress
                """
                session.run(query, batch=congress_batch)
                logger.info(f"Successfully synced {len(congress_batch)} congresses in batch")

        return congress_mapping

    def sync_committees_batch(self, committees_dir: Path, congress_mapping: Dict[int, str]):
        """Sync committee data to Neo4j using batch operations."""
        committee_files = list(committees_dir.glob("*.toml"))
        total_files = len(committee_files)
        logger.info(f"Found {total_files} committee files")

        batch_size = 50  # Process 50 committees at a time
        committees_batch = []
        relationships_batch = []

        for idx, file_path in enumerate(sorted(committee_files), 1):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = tomlkit.load(f)

                    # Prepare committee data (exclude congresses field)
                    committee_data = {k: v for k, v in data.items() if k != "congresses"}
                    committees_batch.append(committee_data)

                    # Prepare relationship data
                    for congress_num in data.get("congresses", []):
                        if congress_num in congress_mapping:
                            relationships_batch.append({
                                "committee_id": data["id"],
                                "congress_id": congress_mapping[congress_num]
                            })

                # Process batch when it reaches the size limit or at the end
                if len(committees_batch) >= batch_size or idx == total_files:
                    self._process_committee_batch(committees_batch, relationships_batch)

                    logger.info(f"Progress: {idx}/{total_files} committees synced")
                    committees_batch = []
                    relationships_batch = []

            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}")

    def _process_committee_batch(self, committees_batch: List[dict], relationships_batch: List[dict]):
        """Process a batch of committees and their relationships."""
        if not committees_batch:
            return

        with self.driver.session() as session:
            # Batch create/update committees
            committee_query = """
            UNWIND $batch AS committee
            MERGE (c:Committee {id: committee.id})
            SET c = committee
            """
            session.run(committee_query, batch=committees_batch)

            # Batch create relationships
            if relationships_batch:
                relationship_query = """
                UNWIND $batch AS rel
                MATCH (com:Committee {id: rel.committee_id})
                MATCH (con:Congress {id: rel.congress_id})
                MERGE (com)-[:BELONGS_TO]->(con)
                """
                session.run(relationship_query, batch=relationships_batch)

    def sync_people_batch(self, people_dir: Path, congress_mapping: Dict[int, str]):
        """Sync person data to Neo4j using batch operations."""
        people_files = list(people_dir.glob("*.toml"))
        total_files = len(people_files)
        logger.info(f"Found {total_files} people files")

        batch_size = 50  # Process 50 people at a time
        people_batch = []
        relationships_batch = []
        start_time = time.time()

        for idx, file_path in enumerate(sorted(people_files), 1):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = tomlkit.load(f)

                    # Prepare person data (exclude memberships and congresses)
                    person_data = {k: v for k, v in data.items() if k not in ["memberships", "congresses"]}
                    people_batch.append(person_data)

                    # Handle new memberships structure
                    memberships = data.get("memberships", [])
                    if memberships:
                        for membership in memberships:
                            congress_num = membership.get("congress")
                            if congress_num and congress_num in congress_mapping:
                                relationships_batch.append({
                                    "person_id": data["id"],
                                    "congress_id": congress_mapping[congress_num],
                                    "position": membership.get("position", ""),
                                    "type": membership.get("type", "congress")
                                })
                    # Fallback for old congresses array
                    elif "congresses" in data:
                        for congress_num in data.get("congresses", []):
                            if congress_num in congress_mapping:
                                relationships_batch.append({
                                    "person_id": data["id"],
                                    "congress_id": congress_mapping[congress_num],
                                    "position": "",
                                    "type": "congress"
                                })

                # Process batch when it reaches the size limit or at the end
                if len(people_batch) >= batch_size or idx == total_files:
                    self._process_people_batch(people_batch, relationships_batch)

                    elapsed = time.time() - start_time
                    rate = idx / elapsed
                    eta = (total_files - idx) / rate if rate > 0 else 0

                    logger.info(f"Progress: {idx}/{total_files} people synced ({rate:.1f} people/sec, ETA: {eta:.0f}s)")
                    people_batch = []
                    relationships_batch = []

            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}")

        total_time = time.time() - start_time
        logger.info(f"Successfully synced people in {total_time:.1f} seconds")

    def _process_people_batch(self, people_batch: List[dict], relationships_batch: List[dict]):
        """Process a batch of people and their relationships."""
        if not people_batch:
            return

        with self.driver.session() as session:
            # Batch create/update people
            people_query = """
            UNWIND $batch AS person
            MERGE (p:Person {id: person.id})
            SET p = person
            """
            session.run(people_query, batch=people_batch)

            # Batch create relationships with properties
            if relationships_batch:
                relationship_query = """
                UNWIND $batch AS rel
                MATCH (p:Person {id: rel.person_id})
                MATCH (c:Congress {id: rel.congress_id})
                MERGE (p)-[r:SERVED_IN]->(c)
                SET r.position = rel.position,
                    r.type = rel.type
                """
                session.run(relationship_query, batch=relationships_batch)

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

            # Count senators vs representatives
            result = session.run("""
                MATCH ()-[r:SERVED_IN]->()
                WHERE r.position = 'senator'
                RETURN count(DISTINCT r) as count
            """)
            stats["senator_terms"] = result.single()["count"]

            result = session.run("""
                MATCH ()-[r:SERVED_IN]->()
                WHERE r.position = 'representative'
                RETURN count(DISTINCT r) as count
            """)
            stats["representative_terms"] = result.single()["count"]

            return stats


def main():
    """Main execution function."""
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
        syncer = Neo4jSyncerOptimized(neo4j_uri, neo4j_username, neo4j_password)

        # Parse command line arguments
        clear_db = "--clear" in sys.argv
        skip_confirmation = "--yes" in sys.argv

        # Optional: Clear database
        if clear_db:
            syncer.clear_database(skip_confirmation=skip_confirmation)

        # Create indexes first for better performance
        logger.info("Creating database indexes...")
        syncer.create_indexes()

        # Track total time
        total_start = time.time()

        # Sync data in order using batch operations
        logger.info("Starting optimized data sync...")

        # 1. Sync Congresses first (they're referenced by committees and people)
        logger.info("Syncing congresses...")
        congress_start = time.time()
        congress_mapping = syncer.sync_congresses_batch(congresses_dir)
        logger.info(f"Congress sync completed in {time.time() - congress_start:.1f}s")

        # 2. Sync Committees
        logger.info("Syncing committees...")
        committee_start = time.time()
        syncer.sync_committees_batch(committees_dir, congress_mapping)
        logger.info(f"Committee sync completed in {time.time() - committee_start:.1f}s")

        # 3. Sync People
        logger.info("Syncing people...")
        people_start = time.time()
        syncer.sync_people_batch(people_dir, congress_mapping)
        logger.info(f"People sync completed in {time.time() - people_start:.1f}s")

        # Display statistics
        stats = syncer.get_statistics()
        total_time = time.time() - total_start

        logger.info("\n=== Sync Complete ===")
        logger.info(f"Total sync time: {total_time:.1f} seconds")
        logger.info(f"Congresses: {stats['Congress']}")
        logger.info(f"Committees: {stats['Committee']}")
        logger.info(f"People: {stats['Person']}")
        logger.info(f"Committee-Congress relationships: {stats['BELONGS_TO']}")
        logger.info(f"Person-Congress relationships: {stats['SERVED_IN']}")
        logger.info(f"  - Senator terms: {stats.get('senator_terms', 0)}")
        logger.info(f"  - Representative terms: {stats.get('representative_terms', 0)}")

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)
    finally:
        if syncer:
            syncer.close()


if __name__ == "__main__":
    main()