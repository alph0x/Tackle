"""Recipe record."""

import dataclasses


@dataclasses.dataclass
class Recipe:
    """Recipe record."""

    slug: str
    title: str
    servings: int
