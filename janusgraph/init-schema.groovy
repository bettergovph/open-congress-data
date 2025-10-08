// JanusGraph Schema Initialization Script
// Run this ONCE before syncing data to create proper indexes

// Open management system
mgmt = graph.openManagement()

// Create property keys if they don't exist
if (mgmt.getPropertyKey('id') == null) {
    id = mgmt.makePropertyKey('id').dataType(String.class).make()
} else {
    id = mgmt.getPropertyKey('id')
}

// Create vertex labels
if (mgmt.getVertexLabel('Congress') == null) {
    mgmt.makeVertexLabel('Congress').make()
}
if (mgmt.getVertexLabel('Group') == null) {
    mgmt.makeVertexLabel('Group').make()
}
if (mgmt.getVertexLabel('Committee') == null) {
    mgmt.makeVertexLabel('Committee').make()
}
if (mgmt.getVertexLabel('Person') == null) {
    mgmt.makeVertexLabel('Person').make()
}
if (mgmt.getVertexLabel('Document') == null) {
    mgmt.makeVertexLabel('Document').make()
}

// Create composite indexes on 'id' property for each label
if (mgmt.getGraphIndex('congressById') == null) {
    mgmt.buildIndex('congressById', Vertex.class)
        .addKey(id)
        .indexOnly(mgmt.getVertexLabel('Congress'))
        .buildCompositeIndex()
}

if (mgmt.getGraphIndex('groupById') == null) {
    mgmt.buildIndex('groupById', Vertex.class)
        .addKey(id)
        .indexOnly(mgmt.getVertexLabel('Group'))
        .buildCompositeIndex()
}

if (mgmt.getGraphIndex('committeeById') == null) {
    mgmt.buildIndex('committeeById', Vertex.class)
        .addKey(id)
        .indexOnly(mgmt.getVertexLabel('Committee'))
        .buildCompositeIndex()
}

if (mgmt.getGraphIndex('personById') == null) {
    mgmt.buildIndex('personById', Vertex.class)
        .addKey(id)
        .indexOnly(mgmt.getVertexLabel('Person'))
        .buildCompositeIndex()
}

if (mgmt.getGraphIndex('documentById') == null) {
    mgmt.buildIndex('documentById', Vertex.class)
        .addKey(id)
        .indexOnly(mgmt.getVertexLabel('Document'))
        .buildCompositeIndex()
}

// Commit the schema
mgmt.commit()

// Wait for indexes to be registered
graph.tx().rollback()

println("Schema initialization complete!")
println("Indexes created:")
println("  - congressById")
println("  - groupById")
println("  - committeeById")
println("  - personById")
println("  - documentById")
