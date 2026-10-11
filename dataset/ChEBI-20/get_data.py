from pathlib import Path
import sys
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

BASE = Path(__file__).resolve().parents[3] / "MultiBench100" / "pilot10h"
CACHE = BASE / "feature_cache" / "ChEBI-20"


class ChEBI20Dataset(Dataset):
    """Molecule/description embeddings; training adds one fixed negative per query."""
    def __init__(self, split="train", root_dir=CACHE, seed=42):
        if split not in {"train", "val", "test"}:
            raise ValueError("split must be train, val, or test")
        path = Path(root_dir) / f"{split}_fp16.pt"
        if not path.is_file():
            raise FileNotFoundError(f"Missing ChEBI-20 feature cache: {path}")
        data = torch.load(path, map_location="cpu", weights_only=True)
        if "smiles" not in data or "text" not in data:
            raise KeyError(f"{path} must contain smiles and text tensors")
        self.smiles = data["smiles"].float()
        self.text = data["text"].float()
        if len(self.smiles) != len(self.text) or len(self.smiles) == 0:
            raise ValueError(f"Invalid molecule/text pair counts in {path}")
        n = len(self.smiles)
        if split == "train" and n > 1:
            rng = np.random.default_rng(seed)
            negative = np.empty(n, dtype=np.int64)
            for i in range(n):
                j = int(rng.integers(n - 1))
                negative[i] = j + (j >= i)
            self.drug_index = torch.arange(n).repeat(2)
            self.text_index = torch.cat((torch.arange(n), torch.from_numpy(negative)))
            self.labels = torch.cat((torch.ones(n), torch.zeros(n))).long()
            order = torch.from_numpy(rng.permutation(2 * n).copy())
            self.drug_index = self.drug_index[order]
            self.text_index = self.text_index[order]
            self.labels = self.labels[order]
        else:
            self.drug_index = torch.arange(n)
            self.text_index = torch.arange(n)
            self.labels = torch.ones(n, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, index):
        return (self.smiles[self.drug_index[index]],
                self.text[self.text_index[index]],
                self.labels[index])


def get_loader(batch_size=64, num_workers=0, shuffle=True, root_dir=CACHE):
    datasets = {s: ChEBI20Dataset(s, root_dir) for s in ("train", "val", "test")}
    loaders = {s: DataLoader(d, batch_size=batch_size,
                             shuffle=(shuffle if s == "train" else False),
                             num_workers=num_workers) for s, d in datasets.items()}
    return loaders["train"], loaders["val"], loaders["test"], 2
