"""
Tests for RoundTripValidator and expression reconstruction.
"""
import pytest
from mathtok.pipeline import MathTokPipeline
from mathtok.validator import RoundTripValidator


@pytest.fixture
def pipeline():
    return MathTokPipeline()


@pytest.fixture
def validator():
    return RoundTripValidator()


class TestRoundTripValidation:
    @pytest.mark.parametrize("expr", [
        "x + 2",
        "2*x + 3",
        "x^2 + 2*x + 1",
        "sin(x^2)",
        "cos(x) + exp(x)",
        "log(x) + sqrt(x)",
        "a*b + a*c",
        "1 / (x + 1)",
    ])
    def test_round_trip_reconstruction(self, pipeline, validator, expr):
        out = pipeline.encode(f"${expr}$")
        res = validator.validate(out, expr)
        assert res.is_valid, f"Failed for {expr}: {res.error_message}"
        assert res.reconstructed_expr is not None

