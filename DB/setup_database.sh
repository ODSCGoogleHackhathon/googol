#!/bin/bash
# Database setup script for Googol project
# This script initializes or updates the SQLite database with the correct schema

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

DB_PATH="./DB/annotations.db"
SCHEMA_PATH="./DB/db_schema.sql"
BACKUP_PATH="./DB/annotations.db.backup"

echo "================================"
echo "Googol Database Setup"
echo "================================"
echo ""

# Check if SQLite is installed
if ! command -v sqlite3 &> /dev/null; then
    echo -e "${RED}❌ SQLite3 is not installed${NC}"
    echo ""
    echo "Please install SQLite3:"
    echo "  macOS:   brew install sqlite3"
    echo "  Ubuntu:  sudo apt-get install sqlite3"
    echo "  Fedora:  sudo dnf install sqlite3"
    exit 1
fi

echo -e "${GREEN}✓ SQLite3 is installed${NC}"

# Check if schema file exists
if [ ! -f "$SCHEMA_PATH" ]; then
    echo -e "${RED}❌ Schema file not found: $SCHEMA_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Schema file found${NC}"

# Check if database exists
if [ -f "$DB_PATH" ]; then
    echo ""
    echo -e "${YELLOW}⚠ Database already exists at: $DB_PATH${NC}"
    
    # Check if annotation_request table exists
    if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='annotation_request';" | grep -q "annotation_request"; then
        echo -e "${GREEN}✓ Database appears to have the correct schema${NC}"
        echo ""
        echo "Current tables:"
        sqlite3 "$DB_PATH" ".tables"
        echo ""
        read -p "Do you want to recreate the database? This will DELETE all existing data! (yes/no): " -r
        echo
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            echo "Keeping existing database."
            exit 0
        fi
    else
        echo -e "${YELLOW}⚠ Database exists but is missing annotation_request table (old schema)${NC}"
        echo ""
        read -p "Do you want to backup and recreate the database? (yes/no): " -r
        echo
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            echo "Keeping existing database."
            exit 0
        fi
    fi
    
    # Backup existing database
    echo ""
    echo -e "${YELLOW}Creating backup...${NC}"
    cp "$DB_PATH" "$BACKUP_PATH"
    echo -e "${GREEN}✓ Backup created: $BACKUP_PATH${NC}"
    
    # Remove old database
    rm "$DB_PATH"
    echo -e "${GREEN}✓ Old database removed${NC}"
fi

# Create new database with schema
echo ""
echo -e "${YELLOW}Creating new database with schema...${NC}"
sqlite3 "$DB_PATH" < "$SCHEMA_PATH"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database created successfully${NC}"
else
    echo -e "${RED}❌ Failed to create database${NC}"
    exit 1
fi

# Verify the setup
echo ""
echo -e "${YELLOW}Verifying database setup...${NC}"
echo ""

# Check tables
TABLES=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
echo "Tables created:"
echo "$TABLES" | while read table; do
    echo "  ✓ $table"
done

# Check for required tables
REQUIRED_TABLES=("label" "patient" "annotation_request" "annotation")
MISSING_TABLES=()

for table in "${REQUIRED_TABLES[@]}"; do
    if ! echo "$TABLES" | grep -q "^${table}$"; then
        MISSING_TABLES+=("$table")
    fi
done

if [ ${#MISSING_TABLES[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Missing required tables: ${MISSING_TABLES[*]}${NC}"
    exit 1
fi

# Check indexes
echo ""
echo "Indexes created:"
sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';" | while read index; do
    echo "  ✓ $index"
done

# Verify foreign keys are enabled
FK_CHECK=$(sqlite3 "$DB_PATH" "PRAGMA foreign_keys;")
if [ "$FK_CHECK" = "1" ]; then
    echo ""
    echo -e "${GREEN}✓ Foreign keys are enabled${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠ Warning: Foreign keys are not enabled${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}✅ Database setup complete!${NC}"
echo "================================"
echo ""
echo "Database location: $DB_PATH"
echo ""
echo "You can now use the database with:"
echo "  - DB/repository.py (AnnotationRepo)"
echo "  - DB/agentic_repository.py (AgenticAnnotationRepo)"
echo ""


