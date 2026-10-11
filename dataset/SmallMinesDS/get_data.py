from pathlib import Path
import json
import re
import numpy as np
import tifffile
import torch
from torch.utils.data import Dataset, DataLoader

BASE = Path(__file__).resolve().parents[3] / "MultiBench100" / "pilot10h"
DATA_ROOT = BASE / "data" / "SmallMinesDS" / "SmallMinesDS"
MANIFEST = BASE / "pilot_results" / "SmallMinesDS" / "split_manifest.json"


def _patch_paths(dataset_root, name):
    match = re.fullmatch(r"MASK_(\d{4})_(2016|2022)\.tif", str(name))
    if not match:
        raise ValueError(f"Unexpected SmallMinesDS patch name: {name!r}")
    patch_id, year = match.groups()
    year_root = Path(dataset_root) / year
    image = year_root / "IMAGE" / f"IMG_GH_{patch_id}_{year}.tif"
    mask = year_root / "MASK" / f"MASK_GH_{patch_id}_{year}.tif"
    if not image.is_file() or not mask.is_file():
        raise FileNotFoundError(f"Missing paired image/mask: {image}, {mask}")
    return image, mask


class SmallMinesDSDataset(Dataset):
    """2022 Sentinel-2/Sentinel-1+DEM tiles with pixel-level binary mine masks."""
    def __init__(self, split="train", dataset_root=DATA_ROOT, manifest_path=MANIFEST):
        if split not in {"train", "val", "test"}:
            raise ValueError("split must be train, val, or test")
        manifest_path = Path(manifest_path)
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Missing split/normalization manifest: {manifest_path}")
        manifest = json.loads(manifest_path.read_text())
        self.names = manifest["samples"][split]
        self.dataset_root = Path(dataset_root)
        self.mean = np.asarray(manifest["channel_mean_train_only"], dtype=np.float32)
        self.std = np.maximum(np.asarray(manifest["channel_std_train_only"], dtype=np.float32), 1e-6)
        for name in self.names:
            _patch_paths(self.dataset_root, name)

    def __len__(self):
        return len(self.names)

    def __getitem__(self, index):
        name = self.names[index]
        image_path, mask_path = _patch_paths(self.dataset_root, name)
        image = tifffile.imread(image_path).astype(np.float32)
        mask = tifffile.imread(mask_path)
        if image.ndim != 3 or image.shape[-1] != 13 or mask.shape != image.shape[:2]:
            raise ValueError(f"Unexpected paired shapes for {name}: {image.shape}, {mask.shape}")
        if not np.isfinite(image).all() or not np.isfinite(mask).all():
            raise ValueError(f"Non-finite values in SmallMinesDS sample {name}")
        values = set(np.unique(mask).tolist())
        if not values.issubset({0, 1, 255}):
            raise ValueError(f"Expected binary mask for {name}; got {sorted(values)[:10]}")
        image = ((image - self.mean) / self.std).transpose(2, 0, 1).copy()
        mask = (mask > 0).astype(np.int64)
        return torch.from_numpy(image), torch.from_numpy(mask), name


def get_loader(batch_size=8, num_workers=0, shuffle=True,
               root_dir=DATA_ROOT, manifest_path=MANIFEST):
    datasets = {
        s: SmallMinesDSDataset(s, root_dir, manifest_path)
        for s in ("train", "val", "test")
    }
    loaders = {s: DataLoader(d, batch_size=batch_size,
                             shuffle=(shuffle if s == "train" else False),
                             num_workers=num_workers) for s, d in datasets.items()}
    return loaders["train"], loaders["val"], loaders["test"], 2
