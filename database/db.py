from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import models


class Database:
    def __init__(self, db_url):
        engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=engine)
        self.maker = sessionmaker(bind=engine)

    def _get_or_create(self, session, model, u_field, u_value, **data):
        db_data = session.query(model).filter(u_field == data[u_value]).first()
        if not db_data:
            db_data = model(**data)
        return db_data

    def create_post(self, data):
        session = self.maker()
        author = self._get_or_create(
            session, models.Author, models.Author.url, "url", **data["author"],
        )

        post = self._get_or_create(
            session, models.Post, models.Post.url, "url", **data["post_data"], author=author
        )
        post.tags.extend(
            map(
                lambda tag_data: self._get_or_create(
                    session, models.Tag, models.Tag.url, "url", **tag_data
                ),
                data["tags"],
            )
        )
        session.add(post)
        try:
            session.commit()
        except Exception as exc:
            # TODO: Отлавливать конкретные ошибки
            print(exc)
            session.rollback()
        finally:
            session.close()
