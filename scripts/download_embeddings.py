from pathlib import Path
import os
from huggingface_hub import snapshot_download

def main() -> None:
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    target_dir = Path("models") / "all-MiniLM-L6-v2"

    # Optional: use mirror if set in environment.
    hf_endpoint = os.getenv("HF_ENDPOINT")
    if hf_endpoint:
        print(f"Using HF_ENDPOINT={hf_endpoint}")

    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {model_id} to {target_dir} ...")

    snapshot_download(
        repo_id=model_id,
        local_dir=str(target_dir),
        local_dir_use_symlinks=False,
    )

    print("Download complete.")

if __name__ == "__main__":
    main()
