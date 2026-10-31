from __future__ import annotations

import pytest

from app.db.models import Base
from app.db.session import configure_database


@pytest.fixture(autouse=True)
def isolated_database(tmp_path):
    engine = configure_database(f"sqlite:///{tmp_path / 'regulens-test.db'}")
    assert engine is not None
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    configure_database()
