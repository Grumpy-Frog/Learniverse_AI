import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.auth.model import User
from app.modules.catalog.model import Chapter, GradeLevel, Subject
from app.modules.dashboard.repository import DashboardRepository
from app.modules.diagnostics.model import UserChapterStatus


class DashboardService:
    @staticmethod
    def _empty_stats() -> dict:
        return {
            "total_chapters": 0,
            "completed_chapters": 0,
            "needs_practice_chapters": 0,
            "not_started_chapters": 0,
            "completion_percentage": 0.0,
        }

    @staticmethod
    def _calculate_stats(chapter_items: list[dict]) -> dict:
        total = len(chapter_items)

        completed = sum(
            1
            for item in chapter_items
            if item["completion_status"] == "completed"
        )

        needs_practice = sum(
            1
            for item in chapter_items
            if item["completion_status"] == "needs_practice"
        )

        not_started = sum(
            1
            for item in chapter_items
            if item["completion_status"] == "not_started"
        )

        percentage = (
            round((completed / total) * 100, 2)
            if total > 0
            else 0.0
        )

        return {
            "total_chapters": total,
            "completed_chapters": completed,
            "needs_practice_chapters": needs_practice,
            "not_started_chapters": not_started,
            "completion_percentage": percentage,
        }

    @staticmethod
    def _chapter_progress_item(
        chapter: Chapter,
        status_record: UserChapterStatus | None,
    ) -> dict:
        completion_status = (
            status_record.completion_status
            if status_record
            else "not_started"
        )

        return {
            "chapter_id": chapter.id,
            "chapter_no": chapter.chapter_no,
            "title": chapter.title,
            "slug": chapter.slug,
            "completion_status": completion_status,
            "latest_score": status_record.latest_score if status_record else None,
            "best_score": status_record.best_score if status_record else None,
            "strength_labels": status_record.strength_labels if status_record else [],
            "weakness_labels": status_record.weakness_labels if status_record else [],
            "show_checkmark": completion_status == "completed",
            "completed_at": status_record.completed_at if status_record else None,
        }

    @staticmethod
    def _build_subject_progress(
        db: Session,
        subject: Subject,
        current_user: User,
    ) -> dict:
        chapters = DashboardRepository.list_active_chapters_for_subject(
            db,
            subject.id,
        )

        statuses = DashboardRepository.list_statuses_for_user(
            db,
            current_user.id,
            [chapter.id for chapter in chapters],
        )

        status_by_chapter_id = {
            status_record.chapter_id: status_record
            for status_record in statuses
        }

        chapter_items = [
            DashboardService._chapter_progress_item(
                chapter,
                status_by_chapter_id.get(chapter.id),
            )
            for chapter in chapters
        ]

        return {
            "subject_id": subject.id,
            "name": subject.name,
            "slug": subject.slug,
            "description": subject.description,
            "display_order": subject.display_order,
            "stats": DashboardService._calculate_stats(chapter_items),
            "chapters": chapter_items,
        }

    @staticmethod
    def _build_grade_progress(
        db: Session,
        grade: GradeLevel,
        current_user: User,
    ) -> dict:
        subjects = DashboardRepository.list_active_subjects_for_grade(
            db,
            grade.id,
        )

        subject_items = [
            DashboardService._build_subject_progress(
                db,
                subject,
                current_user,
            )
            for subject in subjects
        ]

        all_chapters = [
            chapter
            for subject_item in subject_items
            for chapter in subject_item["chapters"]
        ]

        return {
            "grade_id": grade.id,
            "name": grade.name,
            "slug": grade.slug,
            "display_order": grade.display_order,
            "stats": DashboardService._calculate_stats(all_chapters),
            "subjects": subject_items,
        }

    @staticmethod
    def _find_continue_learning(
        grade_items: list[dict],
    ) -> dict | None:
        for target_status in ["needs_practice", "not_started"]:
            for grade in grade_items:
                for subject in grade["subjects"]:
                    for chapter in subject["chapters"]:
                        if chapter["completion_status"] == target_status:
                            return {
                                "grade_id": grade["grade_id"],
                                "grade_name": grade["name"],
                                "subject_id": subject["subject_id"],
                                "subject_name": subject["name"],
                                "chapter_id": chapter["chapter_id"],
                                "chapter_no": chapter["chapter_no"],
                                "chapter_title": chapter["title"],
                                "completion_status": chapter["completion_status"],
                            }

        return None

    @staticmethod
    def get_overview(
        db: Session,
        current_user: User,
    ) -> dict:
        grades = DashboardRepository.list_active_grades(db)

        grade_items = [
            DashboardService._build_grade_progress(
                db,
                grade,
                current_user,
            )
            for grade in grades
        ]

        all_chapters = [
            chapter
            for grade in grade_items
            for subject in grade["subjects"]
            for chapter in subject["chapters"]
        ]

        recent_sessions = DashboardRepository.list_recent_diagnostic_sessions(
            db,
            current_user.id,
            limit=5,
        )

        return {
            "stats": DashboardService._calculate_stats(all_chapters),
            "continue_learning": DashboardService._find_continue_learning(
                grade_items,
            ),
            "recent_diagnostic_sessions": [
                {
                    "session_id": session.id,
                    "chapter_id": session.chapter_id,
                    "assessment_type": session.assessment_type,
                    "status": session.status,
                    "score": session.score,
                    "percentage": session.percentage,
                    "outcome": session.outcome,
                    "created_at": session.created_at,
                    "submitted_at": session.submitted_at,
                }
                for session in recent_sessions
            ],
            "grades": grade_items,
        }

    @staticmethod
    def get_grade_progress(
        db: Session,
        grade_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        grade = DashboardRepository.get_grade(
            db,
            grade_id,
        )

        if not grade or not grade.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grade not found",
            )

        return DashboardService._build_grade_progress(
            db,
            grade,
            current_user,
        )

    @staticmethod
    def get_subject_progress(
        db: Session,
        subject_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        subject = DashboardRepository.get_subject(
            db,
            subject_id,
        )

        if not subject or not subject.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )

        return DashboardService._build_subject_progress(
            db,
            subject,
            current_user,
        )

    @staticmethod
    def get_chapter_progress(
        db: Session,
        chapter_id: uuid.UUID,
        current_user: User,
    ) -> dict:
        chapter = DashboardRepository.get_chapter(
            db,
            chapter_id,
        )

        if not chapter or not chapter.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        statuses = DashboardRepository.list_statuses_for_user(
            db,
            current_user.id,
            [chapter.id],
        )

        status_record = statuses[0] if statuses else None

        return DashboardService._chapter_progress_item(
            chapter,
            status_record,
        )