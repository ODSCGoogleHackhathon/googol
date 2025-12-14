#!/usr/bin/env python3
"""Quick test script for bulletproof annotation pipeline."""

import sys


def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")

    try:
        from src.pipelines.validation_pipeline import GeminiValidator

        print("  ✓ GeminiValidator imported")
    except ImportError as e:
        print(f"  ✗ Failed to import GeminiValidator: {e}")
        return False

    try:
        from src.models.db_serializers import AnnotationSerializer

        print("  ✓ AnnotationSerializer imported")
    except ImportError as e:
        print(f"  ✗ Failed to import AnnotationSerializer: {e}")
        return False

    try:
        from src.pipelines.annotation_pipeline import AnnotationPipeline

        print("  ✓ AnnotationPipeline imported")
    except ImportError as e:
        print(f"  ✗ Failed to import AnnotationPipeline: {e}")
        return False

    try:
        from src.agent.gemini_agent import GeminiAnnotationAgent

        print("  ✓ GeminiAnnotationAgent imported (refactored)")
    except ImportError as e:
        print(f"  ✗ Failed to import GeminiAnnotationAgent: {e}")
        return False

    return True


def test_serializer():
    """Test AnnotationSerializer functionality."""
    print("\nTesting AnnotationSerializer...")

    try:
        from src.models.db_serializers import AnnotationSerializer
        from src.schemas import AnnotationOutput, Finding

        serializer = AnnotationSerializer()

        # Create test annotation
        annotation = AnnotationOutput(
            patient_id="TEST-001",
            findings=[
                Finding(label="Pneumothorax", location="Right lung", severity="Moderate"),
                Finding(label="Normal", location="Left lung", severity="None"),
            ],
            confidence_score=0.85,
            generated_by="MedGemma/Gemini",
            additional_notes="Test annotation with multiple findings",
        )

        # Serialize to DB format
        db_data = serializer.to_db_format(annotation, "/test/image.jpg")

        # Validate structure
        assert "path" in db_data, "Missing 'path' in db_data"
        assert "label" in db_data, "Missing 'label' in db_data"
        assert "patient_id" in db_data, "Missing 'patient_id' in db_data"
        assert "desc" in db_data, "Missing 'desc' in db_data"

        assert db_data["label"] == "Pneumothorax", "Incorrect primary label"
        assert db_data["patient_id"] == 0, "Incorrect patient_id (should be 0 for TEST-001)"
        assert len(db_data["desc"]) <= 3900, "Description exceeds max length"

        print(f"  ✓ Serialization works")
        print(f"    - Label: {db_data['label']}")
        print(f"    - Desc length: {len(db_data['desc'])} chars")
        print(f"    - Patient ID: {db_data['patient_id']}")

        return True

    except Exception as e:
        print(f"  ✗ Serializer test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_schema_validation():
    """Test Pydantic validation on AnnotationOutput."""
    print("\nTesting Pydantic validation...")

    try:
        from src.schemas import AnnotationOutput, Finding
        from pydantic import ValidationError

        # Test valid annotation
        try:
            annotation = AnnotationOutput(
                patient_id="VALID-001",
                findings=[Finding(label="Normal", location="Overall", severity="None")],
                confidence_score=0.9,
            )
            print("  ✓ Valid annotation passes")
        except ValidationError:
            print("  ✗ Valid annotation failed validation")
            return False

        # Test invalid confidence score
        try:
            annotation = AnnotationOutput(
                patient_id="INVALID-001",
                findings=[Finding(label="Test", location="Test", severity="Test")],
                confidence_score=1.5,  # Invalid: > 1.0
            )
            print("  ✗ Invalid confidence score was accepted")
            return False
        except ValidationError:
            print("  ✓ Invalid confidence score rejected")

        # Test missing required field
        try:
            annotation = AnnotationOutput(
                patient_id="INVALID-002",
                findings=[{"label": "Missing fields"}],  # Missing location and severity
                confidence_score=0.5,
            )
            print("  ✗ Invalid finding was accepted")
            return False
        except (ValidationError, TypeError):
            print("  ✓ Invalid finding rejected")

        return True

    except Exception as e:
        print(f"  ✗ Schema validation test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("BULLETPROOF PIPELINE TESTS")
    print("=" * 60)

    all_passed = True

    # Test 1: Imports
    if not test_imports():
        all_passed = False

    # Test 2: Serializer
    if not test_serializer():
        all_passed = False

    # Test 3: Schema validation
    if not test_schema_validation():
        all_passed = False

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start the backend: ./run_backend.sh")
        print("2. Test with real images via API")
        print("3. Monitor logs for validation success/failures")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        print("\nPlease fix the errors above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
