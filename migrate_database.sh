#!/bin/bash
# Database migration script for two-tier agentic architecture

set -e  # Exit on error

echo "=========================================="
echo "Database Migration to Two-Tier Architecture"
echo "=========================================="
echo ""

DB_PATH="./DB/annotations.db"
BACKUP_PATH="./DB/annotations.db.backup.$(date +%Y%m%d_%H%M%S)"
SCHEMA_PATH="./DB/db_schema.sql"

# Step 1: Backup existing database
if [ -f "$DB_PATH" ]; then
    echo "📦 Step 1: Backing up existing database..."
    cp "$DB_PATH" "$BACKUP_PATH"
    echo "   ✓ Backup created: $BACKUP_PATH"
    echo ""
else
    echo "ℹ️  No existing database found, creating new one..."
    echo ""
fi

# Step 2: Remove old database
if [ -f "$DB_PATH" ]; then
    echo "🗑️  Step 2: Removing old database..."
    rm "$DB_PATH"
    echo "   ✓ Old database removed"
    echo ""
fi

# Step 3: Create new database with enhanced schema
echo "🏗️  Step 3: Creating new database with two-tier schema..."
if [ ! -f "$SCHEMA_PATH" ]; then
    echo "   ✗ ERROR: Schema file not found: $SCHEMA_PATH"
    exit 1
fi

sqlite3 "$DB_PATH" < "$SCHEMA_PATH"
echo "   ✓ New database created with:"
echo "      - annotation_request table (staging)"
echo "      - annotation table (clean summaries)"
echo "      - Indexes for performance"
echo ""

# Step 4: Verify schema
echo "🔍 Step 4: Verifying schema..."
TABLE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
INDEX_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='index';")

echo "   ✓ Tables created: $TABLE_COUNT"
echo "   ✓ Indexes created: $INDEX_COUNT"
echo ""

# Step 5: Show table structure
echo "📋 Step 5: Table structures:"
echo ""
echo "   annotation_request (staging):"
sqlite3 "$DB_PATH" ".schema annotation_request" | grep -v "^--" | head -20
echo ""
echo "   annotation (clean):"
sqlite3 "$DB_PATH" ".schema annotation" | grep -v "^--" | head -10
echo ""

# Summary
echo "=========================================="
echo "✅ Migration Complete!"
echo "=========================================="
echo ""
echo "Database: $DB_PATH"
if [ -f "$BACKUP_PATH" ]; then
    echo "Backup:   $BACKUP_PATH"
fi
echo ""
echo "Next steps:"
echo "1. Restart the backend: ./run_backend.sh"
echo "2. Test with API calls"
echo "3. Monitor logs for any issues"
echo ""
echo "To restore backup if needed:"
echo "  cp $BACKUP_PATH $DB_PATH"
echo ""
