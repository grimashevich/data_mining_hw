from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime


Base = declarative_base()


class IdMixin:
    id = Column(Integer, primary_key=True, autoincrement=True)


class UrlMixin:
    url = Column(String, nullable=False, unique=True)


class NameMixin:
    name = Column(String, nullable=False)


tag_post = Table(
    "tag_post",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("post.id")),
    Column("tag_id", Integer, ForeignKey("tag.id")),
)


class Post(Base, IdMixin, UrlMixin):
    __tablename__ = "post"
    title = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("writer.id"))
    post_date = Column(DateTime, nullable=False)
    first_img = Column(String)
    author = relationship("Writer")
    tags = relationship("Tag", secondary=tag_post)


class Writer(Base, IdMixin, UrlMixin, NameMixin):
    __tablename__ = "writer"
    posts = relationship("Post")


class Tag(Base, IdMixin, UrlMixin, NameMixin):
    __tablename__ = "tag"
    posts = relationship("Post", secondary=tag_post)

# class Comment
