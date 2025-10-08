#!/usr/bin/env python3
"""
Optimized sync script for Philippine Congress data to JanusGraph database.

This version uses batch operations and transactions for much faster syncing.
Performance improvements:
- Batch operations for multiple vertices at once
- Reduced network round trips
- Memory-efficient streaming for large document datasets

Usage:
    python sync_to_janusgraph.py                           # Sync data without clearing
    python sync_to_janusgraph.py --clear                   # Clear database first (will prompt for confirmation)
    python sync_to_janusgraph.py --clear --yes             # Clear database first (skip confirmation - for CI/CD)
    python sync_to_janusgraph.py --batch-size 1000         # Use custom batch size for documents
    python sync_to_janusgraph.py --batch-size 5000 --yes   # High-end machine optimization
"""

import os
import sys
import logging
import time
import yaml
import argparse
from pathlib import Path
from typing import Dict, List
import tomlkit
from gremlin_python.driver import client, serializer
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver.aiohttp.transport import AiohttpTransport
from gremlin_python.driver.protocol import GremlinServerError
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class JanusGraphSyncerOptimized:
    """Optimized handler for syncing data to JanusGraph database using batch operations."""

    def __init__(self, uri: str):
        """Initialize JanusGraph connection."""
        try:
            self.uri = uri
            self.client = client.Client(
                uri,
                'g',
                message_serializer=serializer.GraphSONSerializersV3d0(),
                transport_factory=lambda: AiohttpTransport(),
                pool_size=8,
                max_workers=8
            )
            # Test connection
            self.client.submit("g.V().limit(1)").all().result()
            logger.info("Successfully connected to JanusGraph")
        except Exception as e:
            logger.error(f"Failed to connect to JanusGraph: {e}")
            raise

    def _ensure_connection(self):
        """Ensure the connection is alive, reconnect if needed."""
        try:
            self.client.submit("g.V().limit(1)").all().result()
        except Exception as e:
            logger.warning(f"Connection lost, reconnecting: {e}")
            try:
                self.client.close()
            except:
                pass
            self.client = client.Client(
                self.uri,
                'g',
                message_serializer=serializer.GraphSONSerializersV3d0(),
                transport_factory=lambda: AiohttpTransport(),
                pool_size=8,
                max_workers=8
            )
            logger.info("Reconnected to JanusGraph")

    def close(self):
        """Close the JanusGraph client."""
        if self.client:
            self.client.close()

    def clear_database(self, skip_confirmation=False):
        """Clear specific vertex types and their edges from the database."""
        vertex_labels_to_clear = ["Congress", "Committee", "Person", "Group", "Document"]

        try:
            # Count vertices that will be deleted
            count_query = "g.V().hasLabel(within(vertexLabels)).count()"
            result = self.client.submit(count_query, {"vertexLabels": vertex_labels_to_clear}).all().result()
            vertex_count = result[0] if result else 0

            if vertex_count > 0:
                logger.info(
                    f"Will delete vertices with labels: {', '.join(vertex_labels_to_clear)}"
                )

                if skip_confirmation:
                    logger.info(f"Auto-confirming deletion of {vertex_count} vertices (--yes flag provided)")
                    response = "yes"
                else:
                    response = input(
                        f"This will delete {vertex_count} vertices and their edges. Continue? (yes/no): "
                    )

                if response.lower() == "yes":
                    # Drop vertices in batches to avoid timeout
                    for vertex_label in vertex_labels_to_clear:
                        drop_query = "g.V().hasLabel(labelName).drop()"
                        self.client.submit(drop_query, {"labelName": vertex_label}).all().result()
                        logger.info(f"Cleared vertices with label: {vertex_label}")
                    logger.info(
                        f"Cleared {vertex_count} vertices of types: {', '.join(vertex_labels_to_clear)}"
                    )
                else:
                    logger.info("Clear operation cancelled")
            else:
                logger.info(
                    f"No vertices found with labels: {', '.join(vertex_labels_to_clear)}"
                )
        except GremlinServerError as e:
            logger.error(f"Failed to clear database: {e}")
            raise

    def sync_congresses_batch(self, congresses_dir: Path) -> Dict[int, str]:
        """Sync congress data to JanusGraph using batch operations."""
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

        # Batch insert all congresses
        if congress_batch:
            # Process one at a time with direct string interpolation (testing)
            for i, congress in enumerate(congress_batch):
                congress_id = congress["id"]
                congress_number = congress["congress_number"]
                congress_name = congress["name"].replace("'", "\\'")
                ordinal = congress.get("ordinal", "")
                start_date = congress.get("start_date", "")
                end_date = congress.get("end_date", "")
                start_year = congress.get("start_year", 0)
                end_year = congress.get("end_year", 0)
                year_range = congress.get("year_range", "")
                website_key = congress.get("congress_website_key", 0)

                # Test with direct value in query to see if index works
                query = f"""
                g.V().has('Congress', 'id', '{congress_id}').fold()
                    .coalesce(
                        unfold(),
                        addV('Congress').property('id', '{congress_id}')
                    )
                    .property('congress_number', {congress_number})
                    .property('name', '{congress_name}')
                    .property('ordinal', '{ordinal}')
                    .property('start_date', '{start_date}')
                    .property('end_date', '{end_date}')
                    .property('start_year', {start_year})
                    .property('end_year', {end_year})
                    .property('year_range', '{year_range}')
                    .property('congress_website_key', {website_key})
                    .iterate()
                """
                self.client.submit(query).all().result()
                if i == 0:
                    logger.info(f"First congress query (testing index): {query[:100]}...")
            logger.info(f"Successfully synced {len(congress_batch)} congresses")

        return congress_mapping

    def sync_chambers_batch(self, chambers_dir: Path, congress_mapping: Dict[int, str]):
        """Sync chamber (Group) data to JanusGraph using batch operations."""
        chamber_files = list(chambers_dir.glob("*.toml"))
        chamber_files = [f for f in chamber_files if not f.name.startswith('.')]
        total_files = len(chamber_files)
        logger.info(f"Found {total_files} chamber files")

        chambers_batch = []

        for file_path in sorted(chamber_files):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = tomlkit.load(f)
                    chamber_data = dict(data)

                    # Resolve congress ID
                    if data.get("congress") and data["congress"] in congress_mapping:
                        chamber_data["congress_id"] = congress_mapping[data["congress"]]

                    chambers_batch.append(chamber_data)

            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

        # Process chambers one at a time with direct string interpolation
        if chambers_batch:
            for chamber in chambers_batch:
                chamber_id = chamber["id"]
                name = chamber["name"].replace("'", "\\'")
                chamber_type = chamber["type"]
                subtype = chamber["subtype"]
                congress = chamber["congress"]
                congress_id = chamber.get("congress_id", "")

                query = f"""
                def v = g.V().has('Group', 'id', '{chamber_id}').fold()
                    .coalesce(
                        unfold(),
                        addV('Group').property('id', '{chamber_id}')
                    )
                    .property('name', '{name}')
                    .property('type', '{chamber_type}')
                    .property('subtype', '{subtype}')
                    .property('congress', {congress})
                    .next()
                """

                if congress_id:
                    query += f"""
                def congress = g.V().has('Congress', 'id', '{congress_id}').next()
                def existingEdge = g.V(v).outE('BELONGS_TO').where(inV().is(congress)).hasNext()
                if (!existingEdge) {{
                    g.V(v).addE('BELONGS_TO').to(congress).iterate()
                }}
                """

                self.client.submit(query).all().result()
            logger.info(f"Successfully synced {len(chambers_batch)} chambers")

    def sync_committees_batch(self, committees_dir: Path, congress_mapping: Dict[int, str]):
        """Sync committee data to JanusGraph using batch operations."""
        committee_files = list(committees_dir.glob("*.toml"))
        total_files = len(committee_files)
        logger.info(f"Found {total_files} committee files")

        batch_size = 50
        committees_batch = []

        for idx, file_path in enumerate(sorted(committee_files), 1):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = tomlkit.load(f)

                    committee_data = {k: v for k, v in data.items() if k != "congresses"}

                    # Resolve congress IDs
                    congress_ids = []
                    for congress_num in data.get("congresses", []):
                        if congress_num in congress_mapping:
                            congress_ids.append(congress_mapping[congress_num])

                    committee_data["congress_ids"] = congress_ids
                    committees_batch.append(committee_data)

                if len(committees_batch) >= batch_size or idx == total_files:
                    self._process_committee_batch(committees_batch)
                    logger.info(f"Progress: {idx}/{total_files} committees synced")
                    committees_batch = []

            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}")

    def _process_committee_batch(self, committees_batch: List[dict]):
        """Process a batch of committees and their relationships."""
        if not committees_batch:
            return

        query = """
        committees.each { committee ->
            def v = g.V().has('Committee', 'id', committee.id).fold()
                .coalesce(
                    unfold(),
                    addV('Committee').property('id', committee.id)
                )
                .property('name', committee.name)
                .property('type', committee.type ?: '')
                .next()

            // Create relationships to Congress (only if not exists)
            committee.congress_ids.each { congress_id ->
                def congress = g.V().has('Congress', 'id', congress_id).next()
                def existingEdge = g.V(v).outE('BELONGS_TO').where(inV().is(congress)).hasNext()
                if (!existingEdge) {
                    g.V(v).addE('BELONGS_TO').to(congress).iterate()
                }
            }
        }
        """
        self.client.submit(query, {"committees": committees_batch}).all().result()

    def sync_people_batch(self, people_dir: Path, congress_mapping: Dict[int, str] = None):
        """Sync person data to JanusGraph using batch operations."""
        people_files = list(people_dir.glob("*.toml"))
        total_files = len(people_files)
        logger.info(f"Found {total_files} people files")

        batch_size = 50
        people_batch = []
        start_time = time.time()

        for idx, file_path in enumerate(sorted(people_files), 1):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = tomlkit.load(f)

                    person_data = {k: v for k, v in data.items() if k not in ["memberships", "congresses"]}

                    # Handle memberships - create chamber relationships
                    memberships = []
                    for membership in data.get("memberships", []):
                        if membership.get("type") == "chamber":
                            congress_num = membership.get("congress")
                            subtype = membership.get("subtype")
                            if congress_num and subtype:
                                memberships.append({
                                    "congress": congress_num,
                                    "subtype": subtype,
                                    "position": membership.get("position", "")
                                })

                    person_data["memberships"] = memberships
                    people_batch.append(person_data)

                if len(people_batch) >= batch_size or idx == total_files:
                    self._process_people_batch(people_batch)

                    elapsed = time.time() - start_time
                    rate = idx / elapsed
                    eta = (total_files - idx) / rate if rate > 0 else 0

                    logger.info(f"Progress: {idx}/{total_files} people synced ({rate:.1f} people/sec, ETA: {eta:.0f}s)")
                    people_batch = []

            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}")

        total_time = time.time() - start_time
        logger.info(f"Successfully synced people in {total_time:.1f} seconds")

    def _process_people_batch(self, people_batch: List[dict]):
        """Process a batch of people and their relationships."""
        if not people_batch:
            return

        query = """
        people.each { person ->
            def v = g.V().has('Person', 'id', person.id).fold()
                .coalesce(
                    unfold(),
                    addV('Person').property('id', person.id)
                )
                .property('first_name', person.first_name ?: '')
                .property('last_name', person.last_name ?: '')
                .property('middle_name', person.middle_name ?: '')
                .property('name_prefix', person.name_prefix ?: '')
                .property('name_suffix', person.name_suffix ?: '')
                .next()

            // Create chamber relationships (Person -> Group) (only if not exists)
            person.memberships.each { membership ->
                def group = g.V().has('Group', 'type', 'chamber')
                             .has('congress', membership.congress)
                             .has('subtype', membership.subtype).next()
                def existingEdge = g.V(v).outE('MEMBER_OF').where(inV().is(group)).hasNext()
                if (!existingEdge) {
                    g.V(v).addE('MEMBER_OF').to(group)
                        .property('position', membership.position)
                        .iterate()
                }
            }
        }
        """
        self.client.submit(query, {"people": people_batch}).all().result()

    def create_indexes(self):
        """Create composite indexes for better query performance.

        IMPORTANT: Indexes must be created BEFORE any data is added to the graph.
        """
        logger.info("Creating composite indexes (must be done on empty graph)...")

        # Check if indexes already exist and are ENABLED
        check_query = """
        mgmt = graph.openManagement()
        def congressIdx = mgmt.getGraphIndex('congressById')
        def status = null
        if (congressIdx != null) {
            status = mgmt.getIndexStatus(congressIdx, mgmt.getPropertyKey('id')).toString()
        }
        mgmt.rollback()
        [exists: congressIdx != null, status: status]
        """

        try:
            result = self.client.submit(check_query).all().result()
            if result and result[0]:
                index_info = result[0]
                if index_info.get('exists'):
                    logger.info(f"Indexes already exist (status: {index_info.get('status', 'UNKNOWN')})")
                    return
        except Exception as e:
            logger.debug(f"Index check failed (expected on first run): {e}")

        # Create indexes - this MUST be done before adding any data
        index_query = """
        mgmt = graph.openManagement()

        // Create property keys if they don't exist
        def idKey = mgmt.getPropertyKey('id') ?: mgmt.makePropertyKey('id').dataType(String.class).make()
        def typeKey = mgmt.getPropertyKey('type') ?: mgmt.makePropertyKey('type').dataType(String.class).make()
        def congressKey = mgmt.getPropertyKey('congress') ?: mgmt.makePropertyKey('congress').dataType(Integer.class).make()
        def subtypeKey = mgmt.getPropertyKey('subtype') ?: mgmt.makePropertyKey('subtype').dataType(String.class).make()

        // Create vertex labels if they don't exist
        def congressLabel = mgmt.getVertexLabel('Congress') ?: mgmt.makeVertexLabel('Congress').make()
        def groupLabel = mgmt.getVertexLabel('Group') ?: mgmt.makeVertexLabel('Group').make()
        def committeeLabel = mgmt.getVertexLabel('Committee') ?: mgmt.makeVertexLabel('Committee').make()
        def personLabel = mgmt.getVertexLabel('Person') ?: mgmt.makeVertexLabel('Person').make()
        def documentLabel = mgmt.getVertexLabel('Document') ?: mgmt.makeVertexLabel('Document').make()

        // Create composite indexes on 'id' property for each label
        if (mgmt.getGraphIndex('congressById') == null) {
            mgmt.buildIndex('congressById', Vertex.class)
                .addKey(idKey)
                .indexOnly(congressLabel)
                .buildCompositeIndex()
        }

        if (mgmt.getGraphIndex('groupById') == null) {
            mgmt.buildIndex('groupById', Vertex.class)
                .addKey(idKey)
                .indexOnly(groupLabel)
                .buildCompositeIndex()
        }

        if (mgmt.getGraphIndex('committeeById') == null) {
            mgmt.buildIndex('committeeById', Vertex.class)
                .addKey(idKey)
                .indexOnly(committeeLabel)
                .buildCompositeIndex()
        }

        if (mgmt.getGraphIndex('personById') == null) {
            mgmt.buildIndex('personById', Vertex.class)
                .addKey(idKey)
                .indexOnly(personLabel)
                .buildCompositeIndex()
        }

        if (mgmt.getGraphIndex('documentById') == null) {
            mgmt.buildIndex('documentById', Vertex.class)
                .addKey(idKey)
                .indexOnly(documentLabel)
                .buildCompositeIndex()
        }

        // Create composite index for Group lookups by type + congress + subtype
        if (mgmt.getGraphIndex('groupByTypeCongSub') == null) {
            mgmt.buildIndex('groupByTypeCongSub', Vertex.class)
                .addKey(typeKey)
                .addKey(congressKey)
                .addKey(subtypeKey)
                .indexOnly(groupLabel)
                .buildCompositeIndex()
        }

        mgmt.commit()

        // Wait for schema to be committed
        graph.tx().rollback()

        'Indexes created successfully'
        """

        try:
            self.client.submit(index_query).all().result()
            logger.info("✓ Composite indexes created successfully")
            logger.info("  Testing if indexes are being used...")
        except Exception as e:
            logger.error(f"✗ Failed to create indexes: {e}")
            raise Exception("Index creation failed - cannot continue without indexes")

    def get_statistics(self):
        """Get statistics about the synced data."""
        stats = {}

        # Count vertices
        for label in ["Congress", "Committee", "Person", "Group", "Document"]:
            result = self.client.submit("g.V().hasLabel(label).count()", {"label": label}).all().result()
            stats[label] = result[0] if result else 0

        # Count chamber nodes specifically
        result = self.client.submit("g.V().hasLabel('Group').has('type', 'chamber').count()").all().result()
        stats["Chamber"] = result[0] if result else 0

        # Count edges
        for edge_type in ["BELONGS_TO", "MEMBER_OF", "AUTHORED", "FILED_IN"]:
            result = self.client.submit("g.E().hasLabel(label).count()", {"label": edge_type}).all().result()
            stats[edge_type] = result[0] if result else 0

        return stats

    def load_senate_website_key_mapping(self, people_dir: Path) -> Dict:
        """Load the Senate website key to person ID mapping."""
        mapping_file = people_dir / ".senate-website-key-mapping.yml"
        if not mapping_file.exists():
            logger.warning(f"Senate website key mapping file not found: {mapping_file}")
            return {}

        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = yaml.safe_load(f)

        if mapping and isinstance(next(iter(mapping.values())), dict):
            total_mappings = sum(len(codes) for codes in mapping.values())
            logger.info(f"Loaded congress-aware Senate website key mappings: {len(mapping)} congresses, {total_mappings} total code mappings")
        else:
            logger.info(f"Loaded {len(mapping)} Senate website key mappings (legacy format)")

        return mapping

    def load_house_website_key_mapping(self, people_dir: Path) -> Dict[str, str]:
        """Load the House website key to person ID mapping."""
        mapping_file = people_dir / ".house-website-key-mapping.yml"
        if not mapping_file.exists():
            logger.warning(f"House website key mapping file not found: {mapping_file}")
            return {}

        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = yaml.safe_load(f)

        logger.info(f"Loaded {len(mapping)} House website key mappings")
        return mapping

    def sync_documents_batch(self, document_dir: Path, congress_mapping: Dict[int, str], senate_key_mapping: Dict[str, str], house_key_mapping: Dict[str, str], batch_size: int = 500):
        """Sync document data to JanusGraph using streaming batch operations."""
        start_time = time.time()
        total_documents_synced = 0

        # Process each bill type (HB and SB)
        for bill_type in ['hb', 'sb']:
            bill_dir = document_dir / bill_type
            if not bill_dir.exists():
                logger.warning(f"Bill directory not found: {bill_dir}")
                continue

            mapping_filename = f".{bill_type.replace('hb', 'house').replace('sb', 'senate')}-bill-number-mapping.yml"

            congress_dirs = [d for d in bill_dir.iterdir() if d.is_dir() and d.name.isdigit()]
            for congress_dir in sorted(congress_dirs, key=lambda d: int(d.name)):
                congress_num = int(congress_dir.name)
                mapping_file = congress_dir / mapping_filename

                if not mapping_file.exists():
                    logger.warning(f"Mapping file not found: {mapping_file}")
                    continue

                # Count total lines for progress reporting
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    total_bills_in_congress = sum(1 for line in f if line.strip() and not line.strip().startswith('#'))

                if total_bills_in_congress == 0:
                    continue

                logger.info(f"Processing {bill_type.upper()} Congress {congress_num}: {total_bills_in_congress} bills")

                # Process mapping file line by line in chunks of 20
                chunk_size = 20
                processed_count = 0
                chunk_items = []

                with open(mapping_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue

                        # Parse YAML line: 'bill_number': doc_id
                        if ':' in line:
                            parts = line.split(':', 1)
                            bill_number = parts[0].strip().strip("'").strip('"')
                            doc_id = parts[1].strip()
                            chunk_items.append((bill_number, doc_id))

                        # Process when we reach chunk_size
                        if len(chunk_items) >= chunk_size:
                            documents_batch = []

                            for bill_number, doc_id in chunk_items:
                                file_path = congress_dir / f"{doc_id}.toml"

                                if not file_path.exists():
                                    logger.warning(f"Document file not found: {file_path}")
                                    continue

                                try:
                                    with open(file_path, 'r', encoding='utf-8') as doc_file:
                                        data = tomlkit.load(doc_file)

                                    doc_data = {
                                        'id': data.get('id'),
                                        'type': data.get('type', ''),
                                        'subtype': data.get('subtype', ''),
                                        'name': data.get('name', '')
                                    }

                                    if 'meta' in data:
                                        meta = data['meta']
                                        doc_data.update({
                                            'bill_number': meta.get('bill_number', 0),
                                            'congress': meta.get('congress', 0),
                                            'title': meta.get('title', ''),
                                            'date_filed': meta.get('date_filed', ''),
                                            'long_title': meta.get('long_title', ''),
                                            'scope': meta.get('scope', ''),
                                            'authors_raw': meta.get('authors_raw', ''),
                                        })

                                        # Congress relationship
                                        if meta.get('congress') and meta['congress'] in congress_mapping:
                                            doc_data['congress_id'] = congress_mapping[meta['congress']]

                                        # Author relationships
                                        author_ids = []
                                        if meta.get('senate_website_author_codes'):
                                            doc_congress = meta.get('congress')
                                            for author_code in meta['senate_website_author_codes']:
                                                person_id = None
                                                if senate_key_mapping and isinstance(next(iter(senate_key_mapping.values()), None), dict):
                                                    if doc_congress and doc_congress in senate_key_mapping:
                                                        person_id = senate_key_mapping[doc_congress].get(author_code)
                                                else:
                                                    person_id = senate_key_mapping.get(author_code)

                                                if person_id:
                                                    author_ids.append(person_id)

                                        if meta.get('congress_website_author_codes'):
                                            for author_code in meta['congress_website_author_codes']:
                                                if author_code in house_key_mapping:
                                                    author_ids.append(house_key_mapping[author_code])

                                        doc_data['author_ids'] = author_ids

                                    documents_batch.append(doc_data)

                                except Exception as e:
                                    logger.error(f"Failed to load {file_path.name}: {e}")

                            # Sync this chunk
                            if documents_batch:
                                self._process_document_batch(documents_batch)
                                total_documents_synced += len(documents_batch)
                                processed_count += len(documents_batch)

                                # Log progress every 500 documents
                                if processed_count % 500 == 0:
                                    logger.info(
                                        f"  Progress: {processed_count}/{total_bills_in_congress} "
                                        f"({processed_count * 100 / total_bills_in_congress:.1f}%) - "
                                        f"Total synced: {total_documents_synced}"
                                    )

                            # Reset chunk for next batch
                            chunk_items = []

                # Process any remaining items in the last chunk
                if chunk_items:
                    documents_batch = []

                    for bill_number, doc_id in chunk_items:
                        file_path = congress_dir / f"{doc_id}.toml"

                        if not file_path.exists():
                            logger.warning(f"Document file not found: {file_path}")
                            continue

                        try:
                            with open(file_path, 'r', encoding='utf-8') as doc_file:
                                data = tomlkit.load(doc_file)

                            doc_data = {
                                'id': data.get('id'),
                                'type': data.get('type', ''),
                                'subtype': data.get('subtype', ''),
                                'name': data.get('name', '')
                            }

                            if 'meta' in data:
                                meta = data['meta']
                                doc_data.update({
                                    'bill_number': meta.get('bill_number', 0),
                                    'congress': meta.get('congress', 0),
                                    'title': meta.get('title', ''),
                                    'date_filed': meta.get('date_filed', ''),
                                    'long_title': meta.get('long_title', ''),
                                    'scope': meta.get('scope', ''),
                                    'authors_raw': meta.get('authors_raw', ''),
                                })

                                if meta.get('congress') and meta['congress'] in congress_mapping:
                                    doc_data['congress_id'] = congress_mapping[meta['congress']]

                                author_ids = []
                                if meta.get('senate_website_author_codes'):
                                    doc_congress = meta.get('congress')
                                    for author_code in meta['senate_website_author_codes']:
                                        person_id = None
                                        if senate_key_mapping and isinstance(next(iter(senate_key_mapping.values()), None), dict):
                                            if doc_congress and doc_congress in senate_key_mapping:
                                                person_id = senate_key_mapping[doc_congress].get(author_code)
                                        else:
                                            person_id = senate_key_mapping.get(author_code)

                                        if person_id:
                                            author_ids.append(person_id)

                                if meta.get('congress_website_author_codes'):
                                    for author_code in meta['congress_website_author_codes']:
                                        if author_code in house_key_mapping:
                                            author_ids.append(house_key_mapping[author_code])

                                doc_data['author_ids'] = author_ids

                            documents_batch.append(doc_data)

                        except Exception as e:
                            logger.error(f"Failed to load {file_path.name}: {e}")

                    if documents_batch:
                        self._process_document_batch(documents_batch)
                        total_documents_synced += len(documents_batch)
                        processed_count += len(documents_batch)

                        # Log progress every 500 documents
                        if processed_count % 500 == 0:
                            logger.info(
                                f"  Progress: {processed_count}/{total_bills_in_congress} "
                                f"({processed_count * 100 / total_bills_in_congress:.1f}%) - "
                                f"Total synced: {total_documents_synced}"
                            )

        total_time = time.time() - start_time
        logger.info(f"Document sync completed in {total_time:.1f} seconds ({total_documents_synced / total_time:.1f} docs/sec)")

    def _process_document_batch(self, documents_batch: List[dict]):
        """Process a batch of documents and their relationships using string interpolation."""
        if not documents_batch:
            return

        # Ensure connection is alive before processing
        self._ensure_connection()

        # Process each document individually with direct string interpolation
        for doc in documents_batch:
            doc_id = doc["id"]
            doc_type = doc.get("type", "")
            subtype = doc.get("subtype", "")
            name = doc.get("name", "").replace("'", "\\'").replace('"', '\\"')
            bill_number = doc.get("bill_number", 0)
            congress = doc.get("congress", 0)
            title = doc.get("title", "").replace("'", "\\'").replace('"', '\\"')
            date_filed = doc.get("date_filed", "")
            long_title = doc.get("long_title", "").replace("'", "\\'").replace('"', '\\"')
            scope = doc.get("scope", "").replace("'", "\\'").replace('"', '\\"')
            authors_raw = doc.get("authors_raw", "").replace("'", "\\'").replace('"', '\\"')
            congress_id = doc.get("congress_id", "")
            author_ids = doc.get("author_ids", [])

            query = f"""
            def v = g.V().has('Document', 'id', '{doc_id}').fold()
                .coalesce(
                    unfold(),
                    addV('Document').property('id', '{doc_id}')
                )
                .property('type', '{doc_type}')
                .property('subtype', '{subtype}')
                .property('name', '{name}')
                .property('bill_number', {bill_number})
                .property('congress', {congress})
                .property('title', '{title}')
                .property('date_filed', '{date_filed}')
                .property('long_title', '{long_title}')
                .property('scope', '{scope}')
                .property('authors_raw', '{authors_raw}')
                .next()
            """

            # Add FILED_IN relationship
            if congress_id:
                query += f"""
                def congress = g.V().has('Congress', 'id', '{congress_id}').next()
                def filedEdge = g.V(v).outE('FILED_IN').where(inV().is(congress)).hasNext()
                if (!filedEdge) {{
                    g.V(v).addE('FILED_IN').to(congress).iterate()
                }}
                """

            # Add AUTHORED relationships
            for person_id in author_ids:
                query += f"""
                def person_{person_id.replace('-', '_')} = g.V().has('Person', 'id', '{person_id}').tryNext().orElse(null)
                if (person_{person_id.replace('-', '_')} != null) {{
                    def authEdge = g.V(person_{person_id.replace('-', '_')}).outE('AUTHORED').where(inV().is(v)).hasNext()
                    if (!authEdge) {{
                        g.V(person_{person_id.replace('-', '_')}).addE('AUTHORED').to(v).iterate()
                    }}
                }}
                """

            self.client.submit(query).all().result()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Sync Philippine Congress data to JanusGraph database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Sync with default settings (batch_size=500)
  %(prog)s --clear --yes                # Clear database and sync (for CI/CD)
  %(prog)s --batch-size 1000            # Use larger batches (faster, more memory)
  %(prog)s --batch-size 5000 --yes      # High-end machine optimization

Batch Size Recommendations:
  - CI/CD (GitHub Actions):     500-1000  (conservative)
  - Standard laptop (8-16GB):   1000-2000 (balanced)
  - High-end workstation (32GB+): 2000-5000 (fast)
        """
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear database before syncing'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompts (useful for CI/CD)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=500,
        metavar='N',
        help='Number of documents to load into memory per batch (default: 500). Higher values are faster but use more memory.'
    )

    args = parser.parse_args()

    if args.batch_size < 1:
        logger.error("Batch size must be at least 1")
        sys.exit(1)
    if args.batch_size > 10000:
        logger.warning(f"Batch size {args.batch_size} is very large and may cause memory issues")

    load_dotenv()

    janusgraph_uri = os.getenv("JANUSGRAPH_URI", "ws://localhost:8182/gremlin")

    # Get project root directory
    project_root = Path(__file__).parent.parent
    congresses_dir = project_root / "data" / "congress"
    committees_dir = project_root / "data" / "committee"
    people_dir = project_root / "data" / "person"
    chambers_dir = project_root / "data" / "group" / "chamber"
    document_dir = project_root / "data" / "document"

    # Verify directories exist
    for dir_path in [congresses_dir, committees_dir, people_dir]:
        if not dir_path.exists():
            logger.error(f"Directory not found: {dir_path}")
            sys.exit(1)

    if not chambers_dir.exists():
        logger.warning(f"Chambers directory not found: {chambers_dir}. Skipping chamber sync.")
        chambers_dir = None

    syncer = None
    try:
        syncer = JanusGraphSyncerOptimized(janusgraph_uri)

        logger.info(f"Configuration: batch_size={args.batch_size}, clear_db={args.clear}, auto_confirm={args.yes}")

        if args.clear:
            syncer.clear_database(skip_confirmation=args.yes)

        logger.info("Creating database indexes...")
        syncer.create_indexes()

        total_start = time.time()

        logger.info("Starting optimized data sync...")

        logger.info("Syncing congresses...")
        congress_start = time.time()
        congress_mapping = syncer.sync_congresses_batch(congresses_dir)
        logger.info(f"Congress sync completed in {time.time() - congress_start:.1f}s")

        if chambers_dir:
            logger.info("Syncing chambers...")
            chamber_start = time.time()
            syncer.sync_chambers_batch(chambers_dir, congress_mapping)
            logger.info(f"Chamber sync completed in {time.time() - chamber_start:.1f}s")

        logger.info("Syncing committees...")
        committee_start = time.time()
        syncer.sync_committees_batch(committees_dir, congress_mapping)
        logger.info(f"Committee sync completed in {time.time() - committee_start:.1f}s")

        logger.info("Syncing people...")
        people_start = time.time()
        syncer.sync_people_batch(people_dir, congress_mapping)
        logger.info(f"People sync completed in {time.time() - people_start:.1f}s")

        if document_dir.exists():
            logger.info("Loading author key mappings...")
            senate_key_mapping = syncer.load_senate_website_key_mapping(people_dir)
            house_key_mapping = syncer.load_house_website_key_mapping(people_dir)

            logger.info(f"Syncing documents (batch_size={args.batch_size})...")
            document_start = time.time()
            syncer.sync_documents_batch(document_dir, congress_mapping, senate_key_mapping, house_key_mapping, batch_size=args.batch_size)
            logger.info(f"Document sync completed in {time.time() - document_start:.1f}s")
        else:
            logger.warning(f"Document directory not found: {document_dir}. Skipping document sync.")

        stats = syncer.get_statistics()
        total_time = time.time() - total_start

        logger.info("\n=== Sync Complete ===")
        logger.info(f"Total sync time: {total_time:.1f} seconds")
        logger.info(f"Congresses: {stats['Congress']}")
        logger.info(f"Chambers (Group): {stats.get('Chamber', 0)}")
        logger.info(f"Committees: {stats['Committee']}")
        logger.info(f"People: {stats['Person']}")
        logger.info(f"Documents: {stats.get('Document', 0)}")
        logger.info(f"BELONGS_TO edges: {stats['BELONGS_TO']}")
        logger.info(f"MEMBER_OF edges: {stats.get('MEMBER_OF', 0)}")
        logger.info(f"AUTHORED edges: {stats.get('AUTHORED', 0)}")
        logger.info(f"FILED_IN edges: {stats.get('FILED_IN', 0)}")

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)
    finally:
        if syncer:
            syncer.close()


if __name__ == "__main__":
    main()
