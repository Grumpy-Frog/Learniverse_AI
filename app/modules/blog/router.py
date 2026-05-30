import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.model import User
from app.modules.blog.model import BlogPost
from app.modules.blog.schema import (
    BlogGenerateRequest,
    BlogGenerateResponse,
    BlogListItemResponse,
    BlogPostResponse,
)
from app.modules.blog.service import BlogService


router = APIRouter(
    prefix="/blog",
    tags=["Blog"],
)


@router.post(
    "/generate",
    response_model=BlogGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_blog_post(
    payload: BlogGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> BlogGenerateResponse:
    post, reason = await BlogService.generate_blog(
        db,
        payload,
        admin_user,
    )

    return BlogGenerateResponse(
        post=post,
        validation_reason=reason,
    )


@router.get(
    "",
    response_model=list[BlogListItemResponse],
)
def list_published_blog_posts(
    db: Annotated[Session, Depends(get_db)],
) -> list[BlogPost]:
    return BlogService.list_published(db)


@router.get(
    "/admin/all",
    response_model=list[BlogListItemResponse],
)
def list_all_blog_posts_admin(
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> list[BlogPost]:
    return BlogService.list_all_admin(db)


@router.patch(
    "/{blog_id}/publish",
    response_model=BlogPostResponse,
)
def publish_blog_post(
    blog_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> BlogPost:
    return BlogService.publish(db, blog_id)


@router.patch(
    "/{blog_id}/unpublish",
    response_model=BlogPostResponse,
)
def unpublish_blog_post(
    blog_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> BlogPost:
    return BlogService.unpublish(db, blog_id)


@router.get(
    "/{slug}",
    response_model=BlogPostResponse,
)
def get_blog_post_by_slug(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
) -> BlogPost:
    return BlogService.get_published_by_slug(
        db,
        slug,
    )