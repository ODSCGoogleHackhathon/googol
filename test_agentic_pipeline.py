#!/usr/bin/env python3
"""Test script for agentic two-tier annotation pipeline."""

import sys
import os


def test_imports():
    """Test all new modules can be imported."""
    print("=" * 60)
    print("TEST 1: Imports")
    print("=" * 60)

    try:
        from DB.agentic_repository import AgenticAnnotationRepo
        print("  ✓ AgenticAnnotationRepo imported")
    except ImportError as e:
        print(f"  ✗ Failed to import AgenticAnnotationRepo: {e}")
        return False

    try:
        from src.models.summary_models import ClinicalSummary, SummaryGenerationRequest
        print("  ✓ ClinicalSummary models imported")
    except ImportError as e:
        print(f"  ✗ Failed to import summary models: {e}")
        return False

    try:
        from src.agent.summary_generator import GeminiSummaryGenerator
        print("  ✓ GeminiSummaryGenerator imported")
    except ImportError as e:
        print(f"  ✗ Failed to import GeminiSummaryGenerator: {e}")
        return False

    try:
        from src.pipelines.agentic_annotation_pipeline import AgenticAnnotationPipeline
        print("  ✓ AgenticAnnotationPipeline imported")
    except ImportError as e:
        print(f"  ✗ Failed to import AgenticAnnotationPipeline: {e}")
        return False

    return True


def test_clinical_summary_model():
    """Test ClinicalSummary Pydantic model."""
    print("\n" + "=" * 60)
    print("TEST 2: ClinicalSummary Pydantic Model")
    print("=" * 60)

    try:
        from src.models.summary_models import ClinicalSummary
        from pydantic import ValidationError

        # Test valid summary
        summary = ClinicalSummary(
            primary_diagnosis="Pneumothorax",
            summary="Moderate right-sided pneumothorax with 30% lung collapse. No mediastinal shift observed.",
            key_findings=[
                "Right pneumothorax with 30% collapse",
                "No mediastinal shift",
                "Clear costophrenic angles"
            ],
            recommendations="Chest tube placement recommended",
            confidence_note=None
        )

        print(f"  ✓ Valid summary created: {summary.primary_diagnosis}")

        # Test to_desc_string
        desc_str = summary.to_desc_string()
        assert "PRIMARY DIAGNOSIS:" in desc_str
        assert "SUMMARY:" in desc_str
        assert "KEY FINDINGS:" in desc_str
        assert len(desc_str) < 4000  # Must fit in DB field

        print(f"  ✓ to_desc_string works ({len(desc_str)} chars)")

        # Test max_length validation
        try:
            bad_summary = ClinicalSummary(
                primary_diagnosis="Test",
                summary="x" * 4000,  # Too long
                key_findings=["test"]
            )
            print("  ✗ Should have rejected summary > 3500 chars")
            return False
        except ValidationError:
            print("  ✓ Max length validation works")

        # Test max_items validation
        try:
            bad_summary = ClinicalSummary(
                primary_diagnosis="Test",
                summary="Test summary",
                key_findings=["1", "2", "3", "4", "5", "6", "7"]  # Too many
            )
            print("  ✗ Should have rejected > 5 key_findings")
            return False
        except ValidationError:
            print("  ✓ Max items validation works")

        return True

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agentic_repository():
    """Test AgenticAnnotationRepo database operations."""
    print("\n" + "=" * 60)
    print("TEST 3: AgenticAnnotationRepo")
    print("=" * 60)

    try:
        from DB.agentic_repository import AgenticAnnotationRepo
        import tempfile
        import os

        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            temp_db = f.name

        print(f"  Using temp DB: {temp_db}")

        # Initialize schema
        import sqlite3
        conn = sqlite3.connect(temp_db)
        with open('./DB/db_schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.close()

        # Initialize repo
        repo = AgenticAnnotationRepo(db_path=temp_db)
        print("  ✓ Repository initialized")

        # Add patient first (foreign key requirement)
        repo.add_patient(123, "Test Patient")
        print("  ✓ Added patient 123")

        # Save annotation request
        request_id = repo.save_annotation_request(
            set_name=1,
            path_url="/test/image.jpg",
            patient_id=123,
            medgemma_raw="Test MedGemma output",
            gemini_validated={"findings": [{"label": "Normal", "location": "Overall", "severity": "None"}]},
            validation_attempt=1,
            validation_status="success",
            pydantic_output={
                "patient_id": "123",
                "findings": [{"label": "Normal", "location": "Overall", "severity": "None"}],
                "confidence_score": 0.95
            },
            confidence_score=0.95,
            gemini_enhanced=False
        )

        print(f"  ✓ Saved annotation_request (ID={request_id})")

        # Retrieve request
        request = repo.get_annotation_request(request_id)
        assert request is not None
        assert request['path_url'] == "/test/image.jpg"
        assert request['confidence_score'] == 0.95
        print(f"  ✓ Retrieved annotation_request")

        # Get unprocessed
        unprocessed = repo.get_unprocessed_requests()
        assert len(unprocessed) == 1
        print(f"  ✓ Found {len(unprocessed)} unprocessed request(s)")

        # Process to annotation table
        repo.process_request_to_annotation(
            request_id=request_id,
            gemini_summary="PRIMARY DIAGNOSIS: Normal\n\nSUMMARY:\nNo abnormalities detected.",
            primary_label="Normal"
        )

        print(f"  ✓ Processed request to annotation table")

        # Verify processed flag
        request = repo.get_annotation_request(request_id)
        assert request['processed'] == 1
        print(f"  ✓ Request marked as processed")

        # Get annotations
        annotations = repo.get_annotations(set_name=1)
        assert len(annotations) == 1
        print(f"  ✓ Found {len(annotations)} annotation(s)")

        # Get stats
        stats = repo.get_pipeline_stats(set_name=1)
        print(f"  ✓ Stats: {stats}")
        assert stats['total_requests'] == 1
        assert stats['processed'] == 1
        assert stats['avg_confidence'] == 0.95

        # Cleanup
        os.unlink(temp_db)
        print("  ✓ Cleanup complete")

        return True

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AGENTIC PIPELINE TESTS")
    print("=" * 60)

    all_passed = True

    # Test 1: Imports
    if not test_imports():
        all_passed = False

    # Test 2: ClinicalSummary model
    if not test_clinical_summary_model():
        all_passed = False

    # Test 3: Repository
    if not test_agentic_repository():
        all_passed = False

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Recreate database with new schema: rm DB/annotations.db")
        print("2. Initialize with schema: sqlite3 DB/annotations.db < DB/db_schema.sql")
        print("3. Start backend and test with real images")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
