"""
PyTorch LSTM model architecture for next-product prediction.

Architecture:
    Embedding → LSTM → Linear → logits

Usage:
    model = ProductLSTM(vocab_size=1000, embed_dim=64, hidden_dim=128, num_layers=2)
    logits = model(input_seq)          # input_seq: [batch, seq_len]
    probs  = torch.softmax(logits, -1)
"""
import torch
import torch.nn as nn


class ProductLSTM(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 64,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embed_dim,
            padding_idx=0,
        )

        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: LongTensor of shape [batch_size, seq_len]
        Returns:
            logits: FloatTensor of shape [batch_size, vocab_size]
        """
        embed = self.dropout(self.embedding(x))           # [B, T, E]
        lstm_out, _ = self.lstm(embed)                    # [B, T, H]
        last_hidden = lstm_out[:, -1, :]                  # [B, H]
        logits = self.fc(self.dropout(last_hidden))       # [B, V]
        return logits

    def predict_top_k(
        self,
        x: torch.Tensor,
        k: int = 10,
        device: str = "cpu",
    ) -> tuple[list[int], list[float]]:
        """
        Predict top-k product indices and their probability scores.

        Args:
            x      : input sequence tensor [1, seq_len]
            k      : number of top products
            device : 'cpu' or 'cuda'
        Returns:
            (product_indices, probabilities)
        """
        self.eval()
        with torch.no_grad():
            x = x.to(device)
            logits = self.forward(x)                      # [1, V]
            probs = torch.softmax(logits, dim=-1)         # [1, V]
            top_probs, top_indices = torch.topk(probs[0], k=k)
            return top_indices.tolist(), top_probs.tolist()
