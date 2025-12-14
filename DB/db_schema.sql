-- Enhanced Schema with Agentic Pipeline Support
-- Two-tier architecture: annotation_request (raw/staging) → annotation (clean/summary)

PRAGMA foreign_keys = ON;

-- Existing tables
CREATE TABLE label(
    name VARCHAR2(20),
    PRIMARY KEY(name)
);

CREATE TABLE patient(
    id INTEGER,
    name VARCHAR2(20),
    PRIMARY KEY(id)
);

-- NEW: Staging table for raw pipeline outputs
CREATE TABLE annotation_request(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_name INTEGER NOT NULL,
    path_url VARCHAR2(200) NOT NULL,         -- Increased from 40 to 200

    -- Patient info
    patient_id INTEGER,

    -- Raw MedGemma output
    medgemma_raw TEXT,                        -- Full MedGemma analysis

    -- Gemini validated/structured output (JSON)
    gemini_validated TEXT,                    -- Structured findings from Gemini validator (stored as JSON string)
    validation_attempt INTEGER DEFAULT 1,    -- How many attempts to validate
    validation_status VARCHAR2(20),          -- 'success', 'retry', 'fallback'

    -- Pydantic validated output (JSON)
    pydantic_output TEXT NOT NULL,           -- Full AnnotationOutput as JSON string
    confidence_score REAL,                   -- Extracted from pydantic_output

    -- Gemini enhancement (if enabled)
    gemini_enhanced BOOLEAN DEFAULT 0,
    gemini_report TEXT,                      -- Full professional report
    urgency_level VARCHAR2(20),              -- critical/urgent/routine
    clinical_significance VARCHAR2(20),      -- high/medium/low

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT 0,             -- Has it been transferred to annotation table?
    processing_error TEXT,                   -- Any errors during processing

    CONSTRAINT fk_request_patient FOREIGN KEY (patient_id)
        REFERENCES patient(id),

    -- Ensure unique per dataset + image
    UNIQUE(set_name, path_url)
);

-- Annotation table (receives clean, Gemini-summarized data)
CREATE TABLE annotation(
    set_name INTEGER,
    path_url VARCHAR2(200),                  -- Increased from 40 to 200
    label VARCHAR2(20),
    patient_id INTEGER,
    desc VARCHAR(4000),                      -- Now contains Gemini-generated summary

    -- Link back to raw request data
    request_id INTEGER,

    CONSTRAINT fk FOREIGN KEY (label)
        REFERENCES label(name),
    CONSTRAINT fk2 FOREIGN KEY (patient_id)
        REFERENCES patient(id),
    CONSTRAINT fk_request FOREIGN KEY (request_id)
        REFERENCES annotation_request(id) ON DELETE CASCADE,
    PRIMARY KEY(set_name, path_url)
);

-- Indexes for performance
CREATE INDEX idx_request_processed ON annotation_request(processed, set_name);
CREATE INDEX idx_request_created ON annotation_request(created_at);
CREATE INDEX idx_annotation_request ON annotation(request_id);