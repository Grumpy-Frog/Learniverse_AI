import re
import unicodedata
import uuid

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth.model import User
from app.modules.blog.model import BlogPost
from app.modules.blog.prompts import (
    blog_generation_messages,
    blog_validation_messages,
)
from app.modules.blog.repository import BlogRepository
from app.modules.blog.schema import (
    BlogGenerateRequest,
    BlogGeneratedContent,
    BlogValidationResult,
)
from app.modules.tutor.deepseek_provider import DeepSeekProvider


class BlogService:
    @staticmethod
    def _slugify(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        lowercase = ascii_text.lower()

        slug = re.sub(r"[^a-z0-9]+", "-", lowercase)
        slug = slug.strip("-")

        if not slug:
            slug = f"blog-{uuid.uuid4().hex[:8]}"

        return slug[:220]

    @staticmethod
    def _unique_slug(
        db: Session,
        base_slug: str,
    ) -> str:
        slug = BlogService._slugify(base_slug)

        if not BlogRepository.slug_exists(db, slug):
            return slug

        counter = 2

        while True:
            candidate = f"{slug}-{counter}"

            if not BlogRepository.slug_exists(db, candidate):
                return candidate

            counter += 1

    @staticmethod
    async def generate_blog(
        db: Session,
        payload: BlogGenerateRequest,
        current_user: User,
    ) -> tuple[BlogPost, str]:
        await DeepSeekProvider.ensure_credit_available()

        validation_completion = await DeepSeekProvider.complete_json(
            messages=blog_validation_messages(
                topic=payload.topic,
                short_description=payload.short_description,
            ),
            max_tokens=settings.blog_validation_output_tokens,
            temperature=0.0,
        )

        try:
            validation = BlogValidationResult.model_validate(
                validation_completion.data
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DeepSeek returned invalid blog validation JSON",
            ) from exc

        if not validation.is_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Change your blog topic and short description. "
                    "Blog posts must be related to Physics, Chemistry, Biology, or Mathematics."
                ),
            )

        generation_completion = await DeepSeekProvider.complete_json(
            messages=blog_generation_messages(
                topic=payload.topic,
                short_description=payload.short_description,
                category=validation.category,
                language=payload.language,
            ),
            max_tokens=settings.blog_generation_output_tokens,
            temperature=0.7,
        )

        try:
            generated = BlogGeneratedContent.model_validate(
                generation_completion.data
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="DeepSeek returned invalid blog content JSON",
            ) from exc

        final_category = validation.category

        if generated.category != final_category:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Generated blog category does not match validated category",
            )

        final_slug = BlogService._unique_slug(
            db,
            generated.slug or generated.title,
        )

        post = BlogPost(
            author_id=current_user.id,
            title=generated.title,
            slug=final_slug,
            topic=payload.topic.strip(),
            short_description=payload.short_description.strip(),
            category=final_category,
            language=payload.language,
            excerpt=generated.excerpt,
            content_markdown=generated.content_markdown,
            status="draft",
            is_ai_generated=True,
            model_name=settings.deepseek_model,
        )

        created_post = BlogRepository.create(
            db,
            post,
        )

        return created_post, validation.reason

    @staticmethod
    def list_published(
        db: Session,
    ) -> list[BlogPost]:
        return BlogRepository.list_published(db)

    @staticmethod
    def list_all_admin(
        db: Session,
    ) -> list[BlogPost]:
        return BlogRepository.list_all(db)

    @staticmethod
    def get_published_by_slug(
        db: Session,
        slug: str,
    ) -> BlogPost:
        post = BlogRepository.get_by_slug(db, slug)

        if not post or post.status != "published":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found",
            )

        return post

    @staticmethod
    def publish(
        db: Session,
        blog_id: uuid.UUID,
    ) -> BlogPost:
        post = BlogRepository.get_by_id(db, blog_id)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found",
            )

        return BlogRepository.publish(db, post)

    @staticmethod
    def unpublish(
        db: Session,
        blog_id: uuid.UUID,
    ) -> BlogPost:
        post = BlogRepository.get_by_id(db, blog_id)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found",
            )

        return BlogRepository.unpublish(db, post)

