from fastapi import APIRouter, Depends
from simulation.simulator import simulator_engine
from app.core.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import SimulationConfig

router = APIRouter(prefix="/simulation", tags=["Transaction Simulator Controls"])

@router.get("/status")
def get_simulator_status(current_user: User = Depends(get_current_user)):
    return {
        "is_running": simulator_engine.is_running,
        "is_paused": simulator_engine.is_paused,
        "speed_multiplier": simulator_engine.speed_multiplier,
        "selected_typology": simulator_engine.selected_typology,
        "recent_transactions": simulator_engine.recent_generated_txs[-20:]
    }

@router.post("/start")
def start_simulation(current_user: User = Depends(get_current_user)):
    simulator_engine.start()
    return {"message": "Transaction Simulator started", "is_running": True}

@router.post("/pause")
def pause_simulation(current_user: User = Depends(get_current_user)):
    simulator_engine.pause()
    return {"message": "Transaction Simulator paused", "is_paused": True}

@router.post("/resume")
def resume_simulation(current_user: User = Depends(get_current_user)):
    simulator_engine.resume()
    return {"message": "Transaction Simulator resumed", "is_paused": False}

@router.post("/stop")
def stop_simulation(current_user: User = Depends(get_current_user)):
    simulator_engine.stop()
    return {"message": "Transaction Simulator stopped", "is_running": False}

@router.post("/configure")
def configure_simulation(config: SimulationConfig, current_user: User = Depends(get_current_user)):
    simulator_engine.set_speed(config.speed_multiplier)
    simulator_engine.set_typology(config.selected_typology)
    return {
        "message": "Simulation configuration updated",
        "speed_multiplier": simulator_engine.speed_multiplier,
        "selected_typology": simulator_engine.selected_typology
    }
