"""Complete table parity with the migration's predeclared scientific tolerances."""

from __future__ import annotations

import numpy as np
import pandas as pd  # type: ignore[import-untyped]


def assert_table_parity(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    *,
    exact_floats: bool = False,
    stage5_probabilities: bool = False,
) -> None:
    """Reject changed membership/order/schema, missingness, decisions or numeric values."""
    if list(expected) != list(actual) or expected.shape != actual.shape:
        raise ValueError("Frozen table schema/cohort membership changed")
    left, right = expected.reset_index(drop=True), actual.reset_index(drop=True)
    if not left.isna().equals(right.isna()):
        raise ValueError("Frozen missingness/denominators changed")
    for name in left:
        valid = left[name].notna()
        a, b = left.loc[valid, name], right.loc[valid, name]
        if pd.api.types.is_numeric_dtype(a):
            b = pd.to_numeric(b, errors="raise")
            np.testing.assert_allclose(
                a.to_numpy(dtype=float),
                b.to_numpy(dtype=float),
                rtol=0 if exact_floats else 1e-8,
                atol=1e-12 if stage5_probabilities else (0 if exact_floats else 1e-10),
                equal_nan=True,
                err_msg="Frozen numeric parity: " + str(name),
            )
        elif not a.astype("string").equals(b.astype("string")):
            raise ValueError("Frozen categorical/decision/order parity: " + str(name))
