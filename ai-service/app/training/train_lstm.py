"""
train_lstm.py — Offline training script for the LSTM recommendation model.

Run inside Docker:
    python -m app.training.train_lstm

Or from the training directory:
    python train_lstm.py

Flow:
    1. Load user_behavior from PostgreSQL (synchronous via psycopg2 for script use)
    2. Build product vocabulary (product_id → index mapping)
    3. Create sliding-window sequences per user
    4. Train ProductLSTM with CrossEntropyLoss + Adam
    5. Save model weights → models/lstm_model.pth
    6. Save vocab mapping → models/product_vocab.json
"""
import json
import os
import sys
import csv
from collections import defaultdict
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

# ── Allow running as script from project root ─────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import get_settings
from app.models.lstm_model import ProductLSTM

settings = get_settings()

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL_PATH = Path(settings.LSTM_MODEL_PATH)
VOCAB_PATH = Path(settings.LSTM_VOCAB_PATH)
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

EPOCHS = int(os.getenv("LSTM_EPOCHS", "30"))
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
SEQ_LEN = settings.LSTM_SEQ_LEN
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
ProductId = str


# ── Dataset ───────────────────────────────────────────────────────────────────
class ProductSequenceDataset(Dataset):
    """
    Sliding-window dataset from user interaction sequences.

    Each sample:
        input : product indices [SEQ_LEN]
        target: next product index (int)
    """

    def __init__(self, sequences: list[list[int]]) -> None:
        self.samples: list[tuple[list[int], int]] = []
        for seq in sequences:
            for i in range(len(seq) - SEQ_LEN):
                x = seq[i : i + SEQ_LEN]
                y = seq[i + SEQ_LEN]
                self.samples.append((x, y))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        x, y = self.samples[idx]
        return torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.long)


# ── Data loading (synchronous psycopg2 for script) ───────────────────────────
def load_behavior_data() -> list[dict]:
    """Fetch user_behavior rows from PostgreSQL."""
    import psycopg2  # type: ignore

    conn = psycopg2.connect(settings.SYNC_DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, product_id, created_at
        FROM user_behavior
        ORDER BY user_id, created_at
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"user_id": str(r[0]), "product_id": str(r[1])} for r in rows]


def _resolve_behavior_csv_path() -> Path:
    candidates = [
        Path(settings.BEHAVIOR_CSV_PATH),
        Path("/app/data/user_behavior.csv"),
        Path("data/user_behavior.csv"),
        Path(__file__).resolve().parents[2] / "data" / "user_behavior.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Could not find user behavior CSV in: "
        + ", ".join(str(p) for p in candidates)
    )


def load_behavior_csv() -> list[dict]:
    """Load user_behavior rows from CSV for local/offline training."""
    csv_path = _resolve_behavior_csv_path()
    rows: list[dict] = []
    with open(csv_path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            user_id = row.get("user_id")
            product_id = row.get("product_id")
            if not user_id or not product_id:
                continue
            rows.append(
                {
                    "user_id": str(user_id),
                    "product_id": str(product_id),
                    "created_at": row.get("created_at", ""),
                }
            )
    rows.sort(key=lambda r: (r["user_id"], r.get("created_at", "")))
    print(f"Loaded {len(rows)} behavior rows from CSV: {csv_path}")
    return rows


def build_vocab(rows: list[dict]) -> dict[ProductId, int]:
    """Map product_id → integer index (1-based, 0 = padding)."""
    unique_products = sorted({r["product_id"] for r in rows})
    return {pid: idx + 1 for idx, pid in enumerate(unique_products)}


def build_sequences(
    rows: list[dict], vocab: dict[ProductId, int]
) -> list[list[int]]:
    """Group rows by user_id and convert product_ids to vocab indices."""
    user_seqs: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        idx = vocab.get(row["product_id"])
        if idx is not None:
            user_seqs[row["user_id"]].append(idx)
    # Only keep sequences long enough for at least one sample
    return [seq for seq in user_seqs.values() if len(seq) > SEQ_LEN]


# ── Dummy data fallback (for cold-start / testing) ───────────────────────────
def generate_dummy_data(
    n_users: int = 100,
    n_products: int = 200,
    seq_min: int = 15,
    seq_max: int = 30,
) -> tuple[list[list[int]], dict[ProductId, int]]:
    """Generate synthetic sequences when DB is empty."""
    import random

    product_ids = [str(pid) for pid in range(101, 101 + n_products)]
    vocab = {pid: idx + 1 for idx, pid in enumerate(product_ids)}
    seqs = []
    for _ in range(n_users):
        length = random.randint(seq_min, seq_max)
        seq = [vocab[random.choice(product_ids)] for _ in range(length)]
        seqs.append(seq)
    return seqs, vocab


def prepare_sequences(rows: list[dict]) -> tuple[list[list[int]], dict[ProductId, int]]:
    vocab = build_vocab(rows)
    sequences = build_sequences(rows, vocab)
    if not sequences:
        raise ValueError(
            "Not enough behavior rows to build sequences. "
            f"Rows: {len(rows)}, SEQ_LEN: {SEQ_LEN}"
        )
    return sequences, vocab


# ── Training loop ─────────────────────────────────────────────────────────────
def train(
    sequences: list[list[int]],
    vocab: dict[ProductId, int],
) -> ProductLSTM:
    """Train the LSTM model and return it."""
    vocab_size = len(vocab) + 1  # +1 for padding index 0
    dataset = ProductSequenceDataset(sequences)

    if len(dataset) == 0:
        raise ValueError(
            "Not enough data to create training samples. "
            f"Sequences: {len(sequences)}, SEQ_LEN: {SEQ_LEN}"
        )

    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)

    model = ProductLSTM(
        vocab_size=vocab_size,
        embed_dim=settings.LSTM_EMBED_DIM,
        hidden_dim=settings.LSTM_HIDDEN_DIM,
        num_layers=settings.LSTM_NUM_LAYERS,
    ).to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

    print(f"Training on {DEVICE} | samples={len(dataset)} | vocab={vocab_size}")

    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        for x_batch, y_batch in loader:
            x_batch = x_batch.to(DEVICE)
            y_batch = y_batch.to(DEVICE)

            optimizer.zero_grad()
            logits = model(x_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()

        scheduler.step()
        avg_loss = total_loss / len(loader)
        if epoch % 5 == 0 or epoch == 1:
            print(f"  Epoch [{epoch:>3}/{EPOCHS}]  loss={avg_loss:.4f}")

    return model


# ── Save / Load ───────────────────────────────────────────────────────────────
def save_model(model: ProductLSTM, vocab: dict[ProductId, int]) -> None:
    torch.save(
        {
            "state_dict": model.state_dict(),
            "vocab_size": model.vocab_size,
            "embed_dim": model.embed_dim,
            "hidden_dim": model.hidden_dim,
            "num_layers": model.num_layers,
        },
        MODEL_PATH,
    )
    # Save vocab: {"101": 1, "102": 2, ...}  (keys as str for JSON)
    with open(VOCAB_PATH, "w") as f:
        json.dump({str(k): v for k, v in vocab.items()}, f)
    print(f"Model saved -> {MODEL_PATH}")
    print(f"Vocab saved -> {VOCAB_PATH}")


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("  LSTM Recommendation - Training")
    print("=" * 60)

    try:
        rows = load_behavior_data()
        if not rows:
            raise ValueError("Empty DB")
        sequences, vocab = prepare_sequences(rows)
        print(f"Loaded {len(rows)} DB behavior rows, {len(sequences)} user sequences")
    except Exception as exc:
        print(f"[WARN] DB load failed ({exc}). Trying CSV behavior data.")
        try:
            rows = load_behavior_csv()
            sequences, vocab = prepare_sequences(rows)
            print(f"Prepared {len(sequences)} user sequences from CSV")
        except Exception as csv_exc:
            print(f"[WARN] CSV load failed ({csv_exc}). Using dummy data for demo.")
            sequences, vocab = generate_dummy_data()
            print(f"Generated {len(sequences)} dummy sequences")

    model = train(sequences, vocab)
    save_model(model, vocab)
    print("Training complete OK")


if __name__ == "__main__":
    main()
