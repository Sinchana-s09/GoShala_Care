#!/usr/bin/env python
"""
GoShala Care - Model Training Orchestrator
Trains both Tabular Vitals Classifier and Image Disease Classifier
from the datasets in data/vitals and data/train/<class>.
"""
import sys
import os

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.ml_pipeline.train_tabular import train_tabular_pipeline
from backend.ml_pipeline.train_image import train_image_pipeline

def main():
    print("=" * 70)
    print("      GoShala Care: End-to-End Cattle Disease ML Pipeline")
    print("=" * 70)
    
    print("\n>>> PHASE 1: TABULAR VITALS & SYMPTOMS MODEL")
    tabular_results = train_tabular_pipeline()
    
    print("\n>>> PHASE 2: VISUAL LESION & SCAN CLASSIFICATION MODEL")
    image_results = train_image_pipeline()
    
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE! Both models successfully trained and verified.")
    print("Model weights and metrics stored in: backend/models/")
    print("=" * 70)

if __name__ == '__main__':
    main()
