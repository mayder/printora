from __future__ import annotations

import os

from hypothesis import settings


settings.register_profile(
    "ci",
    derandomize=True,
    max_examples=200,
    deadline=500,
    print_blob=True,
)
settings.register_profile(
    "fuzz",
    derandomize=False,
    max_examples=1_000,
    deadline=750,
    print_blob=True,
)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "ci"))
