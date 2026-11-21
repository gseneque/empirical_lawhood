"""Reproduce the declared electron-phonon stability-Xi reference from supplied spectral data."""
from decimal import Decimal

def verify_xi_reference(data, expected):
    """Check the frozen reference with its declared interpolation and numerical profile."""
    import mpmath
    import numpy as np
    from scipy import integrate, interpolate, optimize
    from scipy.integrate import IntegrationWarning
    import warnings

    omega_values = data[:, 0]
    alpha2f_values = data[:, 1]
    alpha2f = interpolate.interp1d(
        omega_values,
        alpha2f_values,
        kind="linear",
        bounds_error=False,
        fill_value=0.0,
    )
    mpmath.mp.dps = 25
    x_table = np.linspace(1e-6, 20, 20_000)
    g_table = np.array(
        [
            float(
                6 * x**2
                + 12 * x**3 * mpmath.im(mpmath.polygamma(1, 1j * x))
                + 6 * x**4 * mpmath.re(mpmath.polygamma(2, 1j * x))
            )
            for x in x_table
        ]
    )
    g = interpolate.interp1d(
        x_table,
        g_table,
        kind="cubic",
        bounds_error=False,
        fill_value=0.0,
    )
    omega_min = float(omega_values.min())
    omega_max = float(omega_values.max())
    split_points = np.unique(
        np.concatenate(
            [
                np.logspace(np.log10(omega_min), np.log10(0.003), 5),
                np.linspace(0.003, omega_max, 4),
            ]
        )
    )

    def xi_at(temperature: float) -> float:
        total = 0.0
        for lower, upper in zip(split_points[:-1], split_points[1:], strict=True):
            # The reference implementation emits a roundoff warning on the
            # locked Hg fixture.  It is recorded in the qualification limits;
            # exact six-place output reproduction remains the adjudicated check.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", IntegrationWarning)
                part, _error = integrate.quad(
                    lambda omega: (
                        g(omega / (2 * np.pi * temperature)) * (2 * alpha2f(omega) / omega)
                    ),
                    lower,
                    upper,
                    limit=200,
                )
            total += float(part)
        return total

    optimum = optimize.minimize_scalar(
        lambda temperature: -xi_at(temperature),
        bounds=(1e-5, omega_max / 2),
        method="bounded",
    )
    observed_temperature = Decimal(f'{optimum.x:.6f}')
    observed_xi = Decimal(f'{-optimum.fun:.6f}')
    if (
        abs(observed_temperature - expected.xi_reference_temperature)
        > expected.xi_reference_tolerance
        or abs(observed_xi - expected.xi_reference_value) > expected.xi_reference_tolerance
    ):
        raise ValueError("locked xi reference fixture does not reproduce")

