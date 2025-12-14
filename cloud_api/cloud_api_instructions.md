# MedGemma on Cloud Compute Instance


## Overview

In order to lower the use of local processing power and to avoid downloading the model locally for each user that installs the app, a Google Cloud Compute Engine instance was launched with a simple API running MedGemma.

The API access should be restricted to app users (as part of plans of a future implementation).

The API code is available in the `cloud_api.py` file and uses FastAPI as well as the `google/medgemma-4b-it` HuggingFace model. 

## Routes

- `POST /annotate/`
    - payload format: `{"prompt": str, "img_b64": str}`, in which "prompt" is the prompt to be sent to the model and "img_b64" is the image base64 encoded.
    - Returns `{"success": boolean, "medgemma_response": str | "msg": str}`, which, in case of success, returns a response from MedGemma.

- `GET /health/`
    - Returns `{"success": True}`

## Considerations on Starting it on Compute Engine

- It was necessary to expand the disk size to 30GB.
- The commands to run the app involve creating its folder, installing dependencies (as in requirements.txt), setting the HF_TOKEN (HuggingFace token) environment variable and running the app with `fastapi`