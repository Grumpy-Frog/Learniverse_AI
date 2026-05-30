import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.blog.model import BlogPost


class BlogRepository:
    @staticmethod
    def create(
        db: Session,
        post: BlogPost,
    ) -> BlogPost:
        db.add(post)
        db.commit()
        db.refresh(post)
        return post

    @staticmethod
    def get_by_id(
        db: Session,
        blog_id: uuid.UUID,
    ) -> BlogPost | None:
        return db.get(BlogPost, blog_id)

    @staticmethod
    def get_by_slug(
        db: Session,
        slug: str,
    ) -> BlogPost | None:
        return db.scalar(
            select(BlogPost).where(BlogPost.slug == slug)
        )

    @staticmethod
    def slug_exists(
        db: Session,
        slug: str,
    ) -> bool:
        return BlogRepository.get_by_slug(db, slug) is not None

    @staticmethod
    def list_published(
        db: Session,
    ) -> list[BlogPost]:
        return list(
            db.scalars(
                select(BlogPost)
                .where(BlogPost.status == "published")
                .order_by(BlogPost.created_at.desc())
            ).all()
        )

    @staticmethod
    def list_all(
        db: Session,
    ) -> list[BlogPost]:
        return list(
            db.scalars(
                select(BlogPost).order_by(BlogPost.created_at.desc())
            ).all()
        )

    @staticmethod
    def publish(
        db: Session,
        post: BlogPost,
    ) -> BlogPost:
        post.status = "published"
        db.commit()
        db.refresh(post)
        return post

    @staticmethod
    def unpublish(
        db: Session,
        post: BlogPost,
    ) -> BlogPost:
        post.status = "draft"
        db.commit()
        db.refresh(post)
        return post