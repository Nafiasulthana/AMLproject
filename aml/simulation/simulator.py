import time
import random
import threading
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class TransactionSimulator:
    """Async background transaction simulator generating live normal & suspicious transaction streams."""
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.speed_multiplier = 1 # 1x to 50x
        self.selected_typology = "MIXED" # MIXED, STRUCTURING, LAYERING, ROUND_TRIP, SMURFING, DORMANT, MULE, PROFILE_MISMATCH
        self.thread = None
        self.recent_generated_txs: List[Dict[str, Any]] = []

        self.account_pool = [
            "ACC_1001", "ACC_1002", "ACC_1003", "ACC_1004", "ACC_1005", "ACC_1006", "ACC_1007"
        ]
        self.channels = ["UPI", "NEFT", "RTGS", "ATM", "CASH_DEPOSIT", "MERCHANT"]

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            logger.info("Transaction simulator started.")

    def pause(self):
        self.is_paused = True
        logger.info("Transaction simulator paused.")

    def resume(self):
        self.is_paused = False
        logger.info("Transaction simulator resumed.")

    def stop(self):
        self.is_running = False
        self.is_paused = False
        logger.info("Transaction simulator stopped.")

    def set_speed(self, speed: int):
        self.speed_multiplier = max(1, min(50, speed))

    def set_typology(self, typology: str):
        self.selected_typology = typology

    def _run_loop(self):
        from app.core.database import SessionLocal
        from app.engine.pipeline import pipeline

        while self.is_running:
            if not self.is_paused:
                db = SessionLocal()
                try:
                    tx_dict = self.generate_single_transaction()
                    result = pipeline.process_transaction(tx_dict, db)
                    
                    tx_record = {
                        "tx_id": result["tx_id"],
                        "sender": tx_dict["sender_account"],
                        "receiver": tx_dict["receiver_account"],
                        "amount": tx_dict["amount"],
                        "channel": tx_dict["channel"],
                        "typology": tx_dict["flagged_typology"],
                        "meta_risk_score": result["meta_risk_score"],
                        "priority": result["priority"],
                        "alert_generated": result["alert_generated"],
                        "alert_id": result.get("alert_id"),
                        "timestamp": time.strftime("%H:%M:%S")
                    }

                    self.recent_generated_txs.append(tx_record)
                    if len(self.recent_generated_txs) > 50:
                        self.recent_generated_txs.pop(0)

                except Exception as ex:
                    logger.error(f"Simulator error during iteration: {ex}")
                finally:
                    db.close()

            sleep_duration = max(0.1, 2.5 / float(self.speed_multiplier))
            time.sleep(sleep_duration)

    def generate_single_transaction(self) -> dict:
        typology = self.selected_typology
        if typology == "MIXED":
            typology = random.choice([
                "NORMAL", "NORMAL", "NORMAL", "NORMAL",
                "STRUCTURING", "LAYERING", "ROUND_TRIP", "DORMANT", "SMURFING", "PROFILE_MISMATCH"
            ])

        sender = random.choice(self.account_pool)
        receiver = random.choice([acc for acc in self.account_pool if acc != sender])

        if typology == "STRUCTURING":
            amount = round(random.uniform(485000.0, 498500.0), 2)
            channel = "CASH_DEPOSIT"
        elif typology == "LAYERING":
            amount = round(random.uniform(750000.0, 3500000.0), 2)
            sender, receiver = "ACC_1001", "ACC_1003"
            channel = "RTGS"
        elif typology == "ROUND_TRIP":
            amount = round(random.uniform(1200000.0, 4500000.0), 2)
            sender, receiver = "ACC_1003", "ACC_1006"
            channel = "NEFT"
        elif typology == "DORMANT":
            amount = round(random.uniform(650000.0, 1800000.0), 2)
            sender = "ACC_1006" # Dormant account
            channel = "RTGS"
        elif typology == "SMURFING":
            amount = round(random.uniform(40000.0, 95000.0), 2)
            receiver = "ACC_1003"
            channel = "UPI"
        elif typology == "PROFILE_MISMATCH":
            amount = round(random.uniform(1500000.0, 4000000.0), 2)
            sender = "ACC_1004" # Low income teacher
            channel = "RTGS"
        else: # NORMAL
            amount = round(random.uniform(250.0, 35000.0), 2)
            channel = random.choice(["UPI", "NEFT", "MERCHANT", "ATM"])

        return {
            "sender_account": sender,
            "receiver_account": receiver,
            "amount": amount,
            "channel": channel,
            "tx_type": "TRANSFER",
            "location": "Mumbai, India",
            "ip_address": f"192.168.1.{random.randint(10, 250)}",
            "device_id": f"DEV_MOB_{random.randint(100, 999)}",
            "flagged_typology": typology
        }

simulator_engine = TransactionSimulator()
