import pytest

from claim.config import save_config
from helpers import AHMAD, make_pdf


@pytest.fixture
def stand_in_form(tmp_path):
    return make_pdf(tmp_path / "form.pdf", "No. Borang : BEP/02", "Versi : 2-01-2025")


@pytest.fixture
def ahmad_config(tmp_path):
    path = tmp_path / "config.toml"
    save_config(AHMAD, path)
    return path
