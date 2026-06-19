"""
LSTMService — Inference service for the trained LSTM recommendation model.

Responsibilities:
    - load_model()  : load saved weights and vocabulary from disk
    - predict()     : given a product sequence, return top-K next products
    - train()       : trigger offline training (runs train_lstm.py)
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

import torch

from app.config import get_settings
from app.models.lstm_model import ProductLSTM

logger = logging.getLogger(__name__)
settings = get_settings()

# Index 0 is reserved for padding; vocab maps product_id (int) → index (int)
ProductId = str
VocabIndex = int


class LSTMService:
    """
    Singleton-style service that holds the loaded LSTM model in memory.
    Call `load_model()` once at application startup.
    """

    def __init__(self) -> None:
        self._model: Optional[ProductLSTM] = None
        # Forward vocab: product_id  → index
        self._vocab: dict[ProductId, VocabIndex] = {}
        # Reverse vocab: index → product_id
        self._reverse_vocab: dict[VocabIndex, ProductId] = {}
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._loaded = False

    # ── Model lifecycle ───────────────────────────────────────────────────────

    def load_model(self) -> None:
        """
        Load model weights and vocabulary from disk.
        Safe to call multiple times — subsequent calls are no-ops.
        """
        if self._loaded:
            return

        model_path = Path(settings.LSTM_MODEL_PATH)
        vocab_path = Path(settings.LSTM_VOCAB_PATH)

        if not model_path.exists() or not vocab_path.exists():
            logger.warning(
                "LSTM model files not found. "
                "Run POST /admin/train-lstm to train the model first."
            )
            return

        # Load vocab
        with open(vocab_path) as f:
            raw_vocab: dict[str, int] = json.load(f)
        self._vocab = {str(k): v for k, v in raw_vocab.items()}
        self._reverse_vocab = {v: str(k) for k, v in self._vocab.items()}

        # Load model checkpoint
        checkpoint = torch.load(model_path, map_location=self._device)
        self._model = ProductLSTM(
            vocab_size=checkpoint["vocab_size"],
            embed_dim=checkpoint["embed_dim"],
            hidden_dim=checkpoint["hidden_dim"],
            num_layers=checkpoint["num_layers"],
        ).to(self._device)
        self._model.load_state_dict(checkpoint["state_dict"])
        self._model.eval()
        self._loaded = True
        logger.info(
            f"LSTM model loaded | vocab={len(self._vocab)} | device={self._device}"
        )

    @property
    def is_loaded(self) -> bool:
        return self._loaded and self._model is not None

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict(
        self,
        product_sequence: list[ProductId],
        top_k: int = 10,
    ) -> list[tuple[ProductId, float]]:
        """
        Predict next products given a history of product_ids.

        Args:
            product_sequence: ordered list of product_ids (most recent last)
                              e.g. [101, 102, 205]
            top_k: number of recommendations to return

        Returns:
            List of (product_id, score) sorted by score descending.
            Returns empty list if model is not loaded.
        """
        if not self.is_loaded:
            logger.warning("predict() called but model is not loaded.")
            return []

        seq_len = settings.LSTM_SEQ_LEN

        # Convert product_ids to vocab indices (skip unknown)
        normalized_sequence = [str(pid) for pid in product_sequence]
        indices = [
            self._vocab[pid]
            for pid in normalized_sequence
            if pid in self._vocab
        ]

        if len(indices) < 1:
            logger.warning("No known products in sequence.")
            return []

        # Pad or truncate to SEQ_LEN
        if len(indices) < seq_len:
            indices = [0] * (seq_len - len(indices)) + indices
        else:
            indices = indices[-seq_len:]

        x = torch.tensor([indices], dtype=torch.long)
        top_indices, top_probs = self._model.predict_top_k(
            x, k=top_k, device=self._device
        )

        results: list[tuple[ProductId, float]] = []
        for idx, prob in zip(top_indices, top_probs):
            pid = self._reverse_vocab.get(idx)
            if pid is not None and pid not in normalized_sequence:
                results.append((pid, float(prob)))

        return results[:top_k]

    # ── Training trigger ──────────────────────────────────────────────────────

    async def train(self) -> dict:
        """
        Trigger offline LSTM training in a background process.
        Reloads the model after training completes.
        """
        logger.info("Starting LSTM training...")
        proc = await asyncio.create_subprocess_exec(
            "python", "-m", "app.training.train_lstm",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode(errors="replace")
            logger.error(f"Training failed: {error_msg}")
            return {"status": "error", "message": error_msg}

        # Reload model after successful training
        self._loaded = False
        self.load_model()
        output = stdout.decode(errors="replace")
        logger.info("LSTM training complete.")
        return {"status": "success", "output": output}


# ── Module-level singleton ────────────────────────────────────────────────────
lstm_service = LSTMService()
