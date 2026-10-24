import os
import sys

# Ensure root directory and database directory are on sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
database_dir = os.path.join(root_dir, "database")
if database_dir not in sys.path:
    sys.path.insert(0, database_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ml.train_model import train_and_save_model

if __name__ == "__main__":
    print("Executing explicit XGBoost model training...")
    train_and_save_model()
