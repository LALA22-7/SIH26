import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from .model import CycloneTemporalModel
from .dataset import CycloneDataset, get_train_val_split

def run_finetuning():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Fine-tuning on {device}")
    
    # Paths
    MANIFEST_PATH = "data/training_manifest.csv"
    NORMALIZED_DIR = "data/normalized"
    PRETRAINED_WEIGHTS = "ml/checkpoints/model.pt"
    SAVE_PATH = "ml/checkpoints/finetuned_model.pt"
    
    # Load dataset
    print("Loading high-res sequence dataset...")
    dataset = CycloneDataset(MANIFEST_PATH, NORMALIZED_DIR, require_pattern_label=True, seq_len=4)
    print(f"Total Sequences: {len(dataset)}")
    
    train_ds, val_ds = get_train_val_split(dataset)
    train_loader = DataLoader(train_ds, batch_size=4, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=4, shuffle=False)
    
    # Initialize model
    model = CycloneTemporalModel(num_classes=5, in_channels=2).to(device)
    
    # Load pre-trained Kaggle weights
    if os.path.exists(PRETRAINED_WEIGHTS):
        print(f"Loading pre-trained weights from {PRETRAINED_WEIGHTS}")
        model.load_state_dict(torch.load(PRETRAINED_WEIGHTS, map_location=device))
    else:
        print(f"WARNING: Pre-trained weights not found at {PRETRAINED_WEIGHTS}. Training from scratch!")
        
    # Extremely low learning rate so we don't destroy pre-trained physics
    optimizer = optim.Adam(model.parameters(), lr=1e-5)
    
    mse_loss = nn.MSELoss()
    ce_loss = nn.CrossEntropyLoss()
    
    NUM_EPOCHS = 15
    print("Starting fine-tuning...")
    
    for epoch in range(NUM_EPOCHS):
        model.train()
        train_loss = 0.0
        for imgs, tgts in train_loader:
            imgs = imgs.to(device)
            centers = tgts["center"].to(device)
            patterns = tgts["pattern"].to(device)
            
            optimizer.zero_grad()
            out = model(imgs)
            loss = mse_loss(out["center"], centers) * 10.0 + ce_loss(out["pattern"], patterns)
            
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{NUM_EPOCHS} - Train Loss: {train_loss/len(train_loader):.4f}")
        
    print(f"Saving fine-tuned model to {SAVE_PATH}")
    torch.save(model.state_dict(), SAVE_PATH)

if __name__ == "__main__":
    run_finetuning()
