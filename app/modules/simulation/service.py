import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.catalog.repository import CatalogRepository
from app.modules.simulation.model import Simulation
from app.modules.simulation.repository import SimulationRepository
from app.modules.simulation.schema import (
    SimulationCreateRequest,
    SimulationUpdateRequest,
)


class SimulationService:
    @staticmethod
    def create_simulation(
        db: Session,
        chapter_id: uuid.UUID,
        payload: SimulationCreateRequest,
    ) -> Simulation:
        chapter = CatalogRepository.get_chapter_by_id(db, chapter_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        if payload.topic_id:
            topic = CatalogRepository.get_topic_by_id(db, payload.topic_id)

            if not topic:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Topic not found",
                )

            if topic.chapter_id != chapter_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Topic does not belong to the selected chapter",
                )

        existing = SimulationRepository.get_by_slug(db, payload.slug)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Simulation with this slug already exists",
            )

        simulation = Simulation(
            chapter_id=chapter_id,
            **payload.model_dump(),
        )

        return SimulationRepository.create(db, simulation)

    @staticmethod
    def update_simulation(
        db: Session,
        simulation_id: uuid.UUID,
        payload: SimulationUpdateRequest,
    ) -> Simulation:
        simulation = SimulationRepository.get_by_id(db, simulation_id)

        if not simulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation not found",
            )

        update_data = payload.model_dump(exclude_unset=True)

        if "topic_id" in update_data and update_data["topic_id"] is not None:
            topic = CatalogRepository.get_topic_by_id(
                db,
                update_data["topic_id"],
            )

            if not topic:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Topic not found",
                )

            if topic.chapter_id != simulation.chapter_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Topic does not belong to the simulation chapter",
                )

        for field, value in update_data.items():
            setattr(simulation, field, value)

        return SimulationRepository.update(db, simulation)

    @staticmethod
    def list_chapter_simulations(
        db: Session,
        chapter_id: uuid.UUID,
    ) -> list[Simulation]:
        chapter = CatalogRepository.get_chapter_by_id(db, chapter_id)

        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        return SimulationRepository.list_by_chapter(db, chapter_id)

    @staticmethod
    def list_topic_simulations(
        db: Session,
        topic_id: uuid.UUID,
    ) -> list[Simulation]:
        topic = CatalogRepository.get_topic_by_id(db, topic_id)

        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )

        return SimulationRepository.list_by_topic(db, topic_id)

    @staticmethod
    def get_simulation(
        db: Session,
        simulation_id: uuid.UUID,
    ) -> Simulation:
        simulation = SimulationRepository.get_by_id(db, simulation_id)

        if not simulation or not simulation.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation not found",
            )

        return simulation