# GitHub and Streamlit Deployment Notes

## Large Model File

The following file must be committed using Git Large File Storage:

`models/multitask_deberta_inference_state.pt`

The repository includes a `.gitattributes` file configured for PyTorch model files.

## Git LFS Commands

```bash
git lfs install
git lfs track "models/*.pt"
git add .gitattributes
```

## Streamlit Entry Point

`app.py`

## Recommended Python Version

Python 3.11 or Python 3.12

## Application Modules

- Voice Incident Reporting
- Manual Incident Reporting
- Batch Incident Processing
- Safety Analytics Dashboard

## Deployment Process

1. Extract the release ZIP.
2. Open a terminal inside the extracted project folder.
3. Initialize Git and Git LFS.
4. Commit all files.
5. Push the repository to GitHub.
6. Connect the GitHub repository to Streamlit Community Cloud.
7. Select `app.py` as the application entry point.
