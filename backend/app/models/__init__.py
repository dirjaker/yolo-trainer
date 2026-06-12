"""Models package — import all models so Alembic can discover them."""

from app.models.user import User  # noqa: F401
from app.models.training import Training  # noqa: F401
from app.models.model import ModelVersion  # noqa: F401
from app.models.dataset import Dataset  # noqa: F401
from app.models.team import Team, TeamMember  # noqa: F401
from app.models.activity import Activity  # noqa: F401
from app.models.hyperparameter import HyperparameterSearch, HyperparameterTrial  # noqa: F401
