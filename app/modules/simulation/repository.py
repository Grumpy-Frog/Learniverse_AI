import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.simulation.model import Simulation


class SimulationRepository:
    @staticmethod
    def create(
        db: Session,
        simulation: Simulation,
    ) -> Simulation:
        db.add(simulation)
        db.commit()
        db.refresh(simulation)

        return simulation

    @staticmethod
    def get_by_id(
        db: Session,
        simulation_id: uuid.UUID,
    ) -> Simulation | None:
        return db.get(Simulation, simulation_id)

    @staticmethod
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> Simulation | None:
        return db.scalar(
            select(Simulation).where(
                Simulation.slug == slug,
            )
        )

    @staticmethod
    def list_by_chapter(
        db: Session,
        chapter_id: uuid.UUID,
    ) -> list[Simulation]:
        return list(
            db.scalars(
                select(Simulation)
                .where(
                    Simulation.chapter_id == chapter_id,
                    Simulation.is_active.is_(True),
                )
                .order_by(
                    Simulation.display_order.asc(),
                    Simulation.created_at.asc(),
                )
            ).all()
        )

    @staticmethod
    def update(
        db: Session,
        simulation: Simulation,
    ) -> Simulation:
        db.commit()
        db.refresh(simulation)

        return simulation

    @staticmethod
    def soft_delete(
        db: Session,
        simulation: Simulation,
    ) -> Simulation:
        simulation.is_active = False

        db.commit()
        db.refresh(simulation)

        return simulation