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
    writer_id = Column(Integer, ForeignKey("writer.id"))
    post_date = Column(DateTime, nullable=False)
    first_img = Column(String)
    author = relationship("Writer")
    comments = relationship("Comment")
    tags = relationship("Tag", secondary=tag_post)


class Writer(Base, IdMixin, UrlMixin, NameMixin):
    __tablename__ = "writer"
    posts = relationship("Post")


class Tag(Base, IdMixin, UrlMixin, NameMixin):
    __tablename__ = "tag"
    posts = relationship("Post", secondary=tag_post)


class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("post.id"))
    post = relationship("Post")
    writer_id = Column(Integer, ForeignKey("writer.id"))
    author = relationship("Writer")
    text = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("comment.id"))
    root_comment_id = Column(Integer, ForeignKey("comment.id"))
