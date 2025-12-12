# Sample Data Directory

## Structure

```
data/
├── sample_images/      # Medical images for testing
├── annotations/        # JSON annotation outputs
└── README.md          # This file
```

## Sample Images

Place medical images here for testing. Suggested sources for **non-PHI, publicly available** medical images:

### Free Medical Image Datasets

1. **NIH Chest X-ray Dataset**
   - https://www.nih.gov/news-events/news-releases/nih-clinical-center-provides-one-largest-publicly-available-chest-x-ray-datasets-scientific-community
   - Free, publicly available chest X-rays

2. **MedPix (Open Access)**
   - https://medpix.nlm.nih.gov/
   - Educational medical images
   - Free for educational/research use

3. **Radiopaedia**
   - https://radiopaedia.org/
   - Many images available under Creative Commons

4. **MIMIC-CXR** (requires registration)
   - https://physionet.org/content/mimic-cxr/
   - Large chest X-ray dataset

### Quick Test Images

For quick testing, you can use:
- Stock medical images from creative commons sources
- Synthetic/mock X-ray images
- Educational anatomy images

### Important Notes

⚠️ **NEVER** upload real patient data without proper authorization
⚠️ **NEVER** include PHI (Protected Health Information)
⚠️ All images should be de-identified
⚠️ This tool is for **DEMO/RESEARCH** only, not clinical use

## Annotations Directory

This directory will store the JSON annotation outputs from MedAnnotator.

Each annotation follows this schema:
```json
{
  "patient_id": "string",
  "findings": [
    {
      "label": "string",
      "location": "string",
      "severity": "string"
    }
  ],
  "confidence_score": 0.0-1.0,
  "generated_by": "MedGemma/Gemini",
  "additional_notes": "string"
}
```

## Usage

1. Add medical images to `sample_images/`
2. Run MedAnnotator
3. Upload images through the UI
4. Download annotations to `annotations/`

## License Compliance

When using sample images:
- Check image licenses
- Provide attribution if required
- Use only for educational/research purposes
- Do not redistribute without permission
