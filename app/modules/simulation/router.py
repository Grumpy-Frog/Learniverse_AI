import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.model import User
from app.modules.simulation.model import Simulation
from app.modules.simulation.schema import (
    DeleteSimulationResponse,
    SimulationCreateRequest,
    SimulationResponse,
    SimulationUpdateRequest,
)
from app.modules.simulation.service import SimulationService


router = APIRouter(
    prefix="/simulations",
    tags=["Simulations"],
)


@router.post(
    "/chapters/{chapter_id}",
    response_model=SimulationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_simulation(
    chapter_id: uuid.UUID,
    payload: SimulationCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> Simulation:
    return SimulationService.create_simulation(
        db,
        chapter_id,
        payload,
    )


@router.get(
    "/chapters/{chapter_id}",
    response_model=list[SimulationResponse],
)
def list_chapter_simulations(
    chapter_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Simulation]:
    return SimulationService.list_chapter_simulations(
        db,
        chapter_id,
    )


@router.patch(
    "/{simulation_id}",
    response_model=SimulationResponse,
)
def update_simulation(
    simulation_id: uuid.UUID,
    payload: SimulationUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> Simulation:
    return SimulationService.update_simulation(
        db,
        simulation_id,
        payload,
    )


@router.delete(
    "/{simulation_id}",
    response_model=DeleteSimulationResponse,
)
def delete_simulation(
    simulation_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> dict:
    return SimulationService.delete_simulation(
        db,
        simulation_id,
    )


@router.get(
    "/{simulation_id}",
    response_model=SimulationResponse,
)
def get_simulation(
    simulation_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Simulation:
    return SimulationService.get_simulation(
        db,
        simulation_id,
    )