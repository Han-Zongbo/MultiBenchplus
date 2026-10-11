from pathlib import Path
import sys
import torch
from torch.utils.data import Dataset, DataLoader

BASE = Path(__file__).resolve().parents[3] / "MultiBench100" / "pilot10h"
CACHE = BASE / "feature_cache" / "MHEALTH"


class MHealthDataset(Dataset):
    """MHEALTH ECG/IMU window embeddings and 12-class activity labels."""
    def __init__(self, split="train", root_dir=CACHE):
        if split not in {"train", "val", "test"}:
            raise ValueError("split must be train, val, or test")
        path = Path(root_dir) / f"{split}_fp16.pt"
        if not path.is_file():
            raise FileNotFoundError(f"Missing {split} feature cache: {path}")
        data = torch.load(path, map_location="cpu", weights_only=True)
        required = ("ecg", "imu", "labels")
        missing = [key for key in required if key not in data]
        if missing:
            raise KeyError(f"{path} is missing fields: {', '.join(missing)}")
        self.ecg = data["ecg"].float()
        self.imu = data["imu"].float()
        self.labels = data["labels"].long()
        lengths = (len(self.ecg), len(self.imu), len(self.labels))
        if len(set(lengths)) != 1:
            raise ValueError(f"Sample counts differ in {path}: {lengths}")

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, index):
        return self.ecg[index], self.imu[index], self.labels[index]


def get_loader(batch_size=64, num_workers=0, shuffle=True, root_dir=CACHE):
    datasets = {s: MHealthDataset(s, root_dir) for s in ("train", "val", "test")}
    loaders = {s: DataLoader(d, batch_size=batch_size,
                             shuffle=(shuffle if s == "train" else False),
                             num_workers=num_workers) for s, d in datasets.items()}
    return loaders["train"], loaders["val"], loaders["test"], 12
