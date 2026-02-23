# pip install openai numpy pandas

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from openai import OpenAI

# Load API key from .gptapi.log (project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
API_KEY_PATH = PROJECT_ROOT / ".gptapi.log"


def load_api_key():
    """Load OpenAI API key from .gptapi.log file."""
    if not API_KEY_PATH.exists():
        raise FileNotFoundError(
            f"API key file not found at {API_KEY_PATH}. "
            "Create .gptapi.log with your OpenAI API key."
        )
    with open(API_KEY_PATH) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith("//"):
                return line
    raise ValueError("No API key found in .gptapi.log")


# Prefer .gptapi.log when it exists (so env var doesn't override your local key)
api_key = load_api_key() if API_KEY_PATH.exists() else os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("No API key found. Create .gptapi.log or set OPENAI_API_KEY.")
client = OpenAI(api_key=api_key)


def get_embedding(text, model="text-embedding-3-large"):
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding


def load_descriptions_from_csvs(data_dir):
    """
    Load object number and chatgpt response - description from all CSV files.
    Returns: list of (trial_name, object_number, description)
    """
    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    records = []
    for csv_path in sorted(data_dir.glob("*.csv")):
        trial_name = csv_path.stem  # e.g., trial1_winter_26
        df = pd.read_csv(csv_path)

        # Find the description column (handle possible name variations)
        desc_col = None
        obj_col = None
        for col in df.columns:
            col_lower = col.lower().strip()
            if "object number" in col_lower or col_lower == "object number":
                obj_col = col
            if "chatgpt response" in col_lower and "description" in col_lower:
                desc_col = col

        if obj_col is None or desc_col is None:
            print(f"Warning: Skipping {csv_path.name} - missing object number or chatgpt response column")
            continue

        for _, row in df.iterrows():
            obj_num = row.get(obj_col)
            desc = row.get(desc_col)

            if pd.isna(obj_num) or pd.isna(desc):
                continue
            obj_num = str(obj_num).strip()
            desc = str(desc).strip()
            if not obj_num or not desc:
                continue
            # Skip header-like rows (e.g., "8B" with no real description)
            if len(desc) < 50:
                continue

            records.append((trial_name, obj_num, desc))

    return records


def main():
    data_dir = PROJECT_ROOT / "data" / "gpt_txt_descriptions"
    records = load_descriptions_from_csvs(data_dir)

    if not records:
        print("No descriptions found in CSV files.")
        return

    print(f"Loaded {len(records)} descriptions from {data_dir}")
    print("Creating embeddings (this may take a minute)...")

    # Create embeddings in batches (API supports up to 2048 inputs per request, we use smaller batches)
    batch_size = 20
    embeddings_list = []
    metadata = [{"trial": t, "object_number": o} for t, o, _ in records]
    descriptions = [desc for _, _, desc in records]

    for i in range(0, len(descriptions), batch_size):
        batch = descriptions[i : i + batch_size]
        response = client.embeddings.create(input=batch, model="text-embedding-3-large")
        for item in sorted(response.data, key=lambda x: x.index):
            embeddings_list.append(item.embedding)

    embeddings = np.array(embeddings_list)
    print(f"Shape of embeddings: {embeddings.shape}")

    # Save for cross-trial comparison
    output_dir = PROJECT_ROOT / "embeddings" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    np.save(output_dir / "embeddings.npy", embeddings)

    # Save metadata for mapping embeddings back to (trial, object_number)
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved embeddings to {output_dir}")
    print("\nTo compare descriptions across trials for the same object:")
    print("  - embeddings[i] corresponds to metadata[i] (trial, object_number)")
    print("  - Use cosine_similarity.py on embeddings for same object_number across trials")


if __name__ == "__main__":
    main()
