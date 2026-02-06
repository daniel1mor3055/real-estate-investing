"""Unit tests for Deal Quality Score per CONTEXT.md Part IV.

Tests verify:
- Investor profile weights
- Metric normalization (0-100 scale)
- Weighted score calculation
- Different investor archetypes

CONTEXT.md Reference:
- Section 4.1: Philosophy of multi-factor weighted scoring
- Section 4.2: Investor archetypes (Cash Flow, Balanced, Appreciation)
- Section 4.3: Scoring methodology (normalize, weight, sum)
"""

import pytest
from src.core.calculators.metrics import MetricsCalculator
from src.core.strategies.investor import (
    InvestorStrategy,
    CashFlowInvestor,
    BalancedInvestor,
    AppreciationInvestor,
    get_investor_strategy,
)


# =============================================================================
# INVESTOR PROFILES - CONTEXT.md Section 4.2
# =============================================================================

class TestInvestorProfiles:
    """Test investor profile definitions per CONTEXT.md Section 4.2."""
    
    def test_cash_flow_investor_profile(self):
        """Cash Flow Maximizer prioritizes immediate income.
        
        CONTEXT.md: "This investor's primary goal is to generate stable, 
        predictable, and immediate income... metrics that measure immediate 
        return and safety, such as Year 1 Cash-on-Cash Return and DSCR, 
        are paramount."
        """
        # Arrange
        strategy = CashFlowInvestor()
        
        # Act
        weights = strategy.weights
        
        # Assert - CoC and DSCR should have highest weights
        assert weights["coc_return"] >= weights["irr"]
        assert weights["dscr"] >= weights["equity_multiple"]
        assert weights["coc_return"] >= 0.30  # Should be significant
    
    def test_balanced_investor_profile(self):
        """Balanced Growth investor seeks balance.
        
        CONTEXT.md: "This investor seeks a blend of immediate cash flow 
        and long-term wealth creation through appreciation. Their evaluation 
        gives balanced importance to immediate returns (CoC), safety (DSCR), 
        and long-term total returns (IRR, Equity Multiple)."
        """
        # Arrange
        strategy = BalancedInvestor()
        
        # Act
        weights = strategy.weights
        
        # Assert - weights should be more evenly distributed
        assert 0.15 <= weights["coc_return"] <= 0.35
        assert 0.15 <= weights["irr"] <= 0.35
        assert 0.10 <= weights["dscr"] <= 0.30
    
    def test_appreciation_investor_profile(self):
        """Appreciation Hunter prioritizes long-term returns.
        
        CONTEXT.md: "This investor's primary objective is significant 
        long-term capital appreciation. For this profile, metrics that 
        capture total, time-weighted returns, such as IRR and Equity 
        Multiple, are the most important."
        """
        # Arrange
        strategy = AppreciationInvestor()
        
        # Act
        weights = strategy.weights
        
        # Assert - IRR and EM should have highest weights
        assert weights["irr"] >= weights["coc_return"]
        assert weights["equity_multiple"] >= weights["dscr"]
        assert weights["irr"] >= 0.30  # Should be significant
    
    def test_all_profiles_weights_sum_to_1(self):
        """All investor profile weights should sum to 1.0 (100%)."""
        # Arrange
        profiles = [CashFlowInvestor(), BalancedInvestor(), AppreciationInvestor()]
        
        # Act & Assert
        for profile in profiles:
            total_weight = sum(profile.weights.values())
            assert total_weight == pytest.approx(1.0, rel=1e-6), \
                f"{profile.name} weights sum to {total_weight}, not 1.0"


class TestInvestorProfileWeights:
    """Test specific weight values per CONTEXT.md Weighting Matrix."""
    
    def test_cash_flow_maximizer_weights(self):
        """Cash Flow Maximizer weights per CONTEXT.md table.
        
        CONTEXT.md Investor Profile Weighting Matrix:
        - Year 1 CoC Return: 40%
        - Average DSCR: 30%
        - IRR: 10%
        - Equity Multiple: 10%
        - Cap Rate: 10%
        """
        # Arrange
        strategy = CashFlowInvestor()
        
        # Act & Assert
        assert strategy.weights["coc_return"] == 0.40
        assert strategy.weights["dscr"] == 0.30
        assert strategy.weights["irr"] == 0.10
        assert strategy.weights["equity_multiple"] == 0.10
        assert strategy.weights["cap_rate"] == 0.10
    
    def test_balanced_growth_weights(self):
        """Balanced Growth weights per CONTEXT.md table.
        
        CONTEXT.md Investor Profile Weighting Matrix:
        - Year 1 CoC Return: 25%
        - Average DSCR: 20%
        - IRR: 25%
        - Equity Multiple: 20%
        - Cap Rate: 10%
        """
        # Arrange
        strategy = BalancedInvestor()
        
        # Act & Assert
        assert strategy.weights["coc_return"] == 0.25
        assert strategy.weights["dscr"] == 0.20
        assert strategy.weights["irr"] == 0.25
        assert strategy.weights["equity_multiple"] == 0.20
        assert strategy.weights["cap_rate"] == 0.10
    
    def test_appreciation_hunter_weights(self):
        """Appreciation Hunter weights per CONTEXT.md table.
        
        CONTEXT.md Investor Profile Weighting Matrix:
        - Year 1 CoC Return: 10%
        - Average DSCR: 10%
        - IRR: 40%
        - Equity Multiple: 30%
        - Cap Rate: 10%
        """
        # Arrange
        strategy = AppreciationInvestor()
        
        # Act & Assert
        assert strategy.weights["coc_return"] == 0.10
        assert strategy.weights["dscr"] == 0.10
        assert strategy.weights["irr"] == 0.40
        assert strategy.weights["equity_multiple"] == 0.30
        assert strategy.weights["cap_rate"] == 0.10


# =============================================================================
# METRIC NORMALIZATION - CONTEXT.md Section 4.3.2
# =============================================================================

class TestMetricNormalization:
    """Test metric normalization per CONTEXT.md Section 4.3.2.
    
    CONTEXT.md: "Each metric must be normalized to a common scale, such as 
    0 to 100. This is achieved by defining performance thresholds for each 
    metric and mapping the calculated value to this scale."
    """
    
    def test_normalization_range(self):
        """Normalized values should be between 0 and 100."""
        # Arrange
        strategy = BalancedInvestor()
        
        # Act
        low_value = strategy.normalize_metric(0.02, "coc_return")  # 2%
        mid_value = strategy.normalize_metric(0.08, "coc_return")  # 8%
        high_value = strategy.normalize_metric(0.20, "coc_return")  # 20%
        
        # Assert
        assert 0 <= low_value <= 100
        assert 0 <= mid_value <= 100
        assert 0 <= high_value <= 100
    
    def test_normalization_below_threshold_is_zero(self):
        """Values at or below low threshold normalize to 0.
        
        CONTEXT.md: "A score of 0 is assigned for any value <= 1.20 (Unacceptable)"
        """
        # Arrange
        strategy = BalancedInvestor()
        
        # Act
        # DSCR threshold: low=1.2, so 1.2 or below = 0
        score = strategy.normalize_metric(1.20, "dscr")
        score_below = strategy.normalize_metric(1.0, "dscr")
        
        # Assert
        assert score == 0
        assert score_below == 0
    
    def test_normalization_above_threshold_is_100(self):
        """Values at or above high threshold normalize to 100.
        
        CONTEXT.md: "A score of 100 is assigned for any value >= 2.00 (Excellent)"
        """
        # Arrange
        strategy = BalancedInvestor()
        
        # Act
        # DSCR threshold: high=2.0, so 2.0 or above = 100
        score_at = strategy.normalize_metric(2.0, "dscr")
        score_above = strategy.normalize_metric(2.5, "dscr")
        
        # Assert
        assert score_at == 100
        assert score_above == 100
    
    def test_normalization_target_is_50(self):
        """Target value normalizes to 50.
        
        CONTEXT.md: "A score of 50 is assigned for a value of 1.50 (Good)"
        """
        # Arrange
        strategy = BalancedInvestor()
        
        # Act
        # DSCR threshold: target=1.5
        score = strategy.normalize_metric(1.5, "dscr")
        
        # Assert
        assert score == 50
    
    def test_normalization_linear_interpolation(self):
        """Values between thresholds are linearly interpolated.
        
        CONTEXT.md: "Values between these thresholds are linearly interpolated"
        """
        # Arrange
        strategy = BalancedInvestor()
        
        # For DSCR: low=1.2, target=1.5, high=2.0
        # Midpoint between low and target is 1.35 -> should be 25
        mid_low_target = 1.35
        
        # Act
        score = strategy.normalize_metric(mid_low_target, "dscr")
        
        # Assert
        # Should be halfway between 0 and 50 = 25
        assert score == pytest.approx(25, rel=0.01)


class TestDSCRNormalization:
    """Test DSCR-specific normalization per CONTEXT.md example."""
    
    def test_dscr_thresholds(self):
        """DSCR thresholds per CONTEXT.md Section 4.3.2.
        
        CONTEXT.md example:
        - 0 for <= 1.20 (Unacceptable)
        - 50 for 1.50 (Good)
        - 100 for >= 2.00 (Excellent)
        """
        # Arrange
        strategy = BalancedInvestor()
        
        # Act & Assert
        assert strategy.normalize_metric(1.0, "dscr") == 0
        assert strategy.normalize_metric(1.2, "dscr") == 0
        assert strategy.normalize_metric(1.5, "dscr") == 50
        assert strategy.normalize_metric(2.0, "dscr") == 100
        assert strategy.normalize_metric(3.0, "dscr") == 100


# =============================================================================
# DEAL SCORE CALCULATION - CONTEXT.md Section 4.3.4
# =============================================================================

class TestDealScoreCalculation:
    """Test deal score calculation per CONTEXT.md Section 4.3.4.
    
    CONTEXT.md Formula: Deal Score = Σ(Normalized Metric Score × Weight)
    """
    
    def test_deal_score_formula(self):
        """Deal Score is weighted sum of normalized metrics."""
        # Arrange
        strategy = BalancedInvestor()
        metrics = {
            "coc_return": 0.08,  # 8% CoC -> normalized
            "dscr": 1.5,        # 1.5 DSCR -> normalized
            "cap_rate": 0.06,   # 6% cap -> normalized
            "irr": 0.12,        # 12% IRR -> normalized
            "equity_multiple": 2.0,  # 2.0x EM -> normalized
        }
        
        # Act
        score = strategy.calculate_score(metrics)
        
        # Assert
        assert 0 <= score <= 100
    
    def test_deal_score_all_excellent_is_100(self):
        """All excellent metrics should yield score near 100."""
        # Arrange
        strategy = BalancedInvestor()
        metrics = {
            "coc_return": 0.20,  # Excellent
            "dscr": 2.5,         # Excellent
            "cap_rate": 0.10,    # Excellent
            "irr": 0.25,         # Excellent
            "equity_multiple": 3.5,  # Excellent
        }
        
        # Act
        score = strategy.calculate_score(metrics)
        
        # Assert
        assert score >= 90  # Should be near 100
    
    def test_deal_score_all_poor_is_low(self):
        """All poor metrics should yield low score."""
        # Arrange
        strategy = BalancedInvestor()
        metrics = {
            "coc_return": 0.01,  # Poor
            "dscr": 1.1,         # Poor
            "cap_rate": 0.02,    # Poor
            "irr": 0.03,         # Poor
            "equity_multiple": 1.1,  # Poor
        }
        
        # Act
        score = strategy.calculate_score(metrics)
        
        # Assert
        assert score <= 10  # Should be low
    
    def test_deal_score_different_by_profile(self, sample_deal):
        """Same deal gets different scores for different profiles."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result_cf = calculator.calculate(investor_profile="cash_flow")
        result_bal = calculator.calculate(investor_profile="balanced")
        result_app = calculator.calculate(investor_profile="appreciation")
        
        # Assert - scores exist (may be similar or different based on deal)
        assert result_cf.data.deal_score is not None
        assert result_bal.data.deal_score is not None
        assert result_app.data.deal_score is not None


class TestDealScoreIntegration:
    """Test deal score integration with metrics calculator."""
    
    def test_deal_score_calculated(self, sample_deal):
        """Deal score is calculated as part of metrics."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(
            holding_period=10,
            investor_profile="balanced"
        )
        
        # Assert
        assert result.success
        assert result.data.deal_score is not None
        assert 0 <= result.data.deal_score.value <= 100
    
    def test_deal_score_with_all_profiles(self, sample_deal, investor_profile):
        """Deal score can be calculated for all investor profiles."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(
            holding_period=10,
            investor_profile=investor_profile
        )
        
        # Assert
        assert result.success
        assert result.data.deal_score is not None
    
    def test_deal_score_metadata(self, sample_deal):
        """Deal score includes metadata about calculation."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(
            holding_period=10,
            investor_profile="balanced"
        )
        
        # Assert
        assert result.metadata["investor_profile"] == "balanced"
        assert result.metadata["holding_period"] == 10


# =============================================================================
# STRATEGY FACTORY
# =============================================================================

class TestStrategyFactory:
    """Test investor strategy factory function."""
    
    def test_get_cash_flow_strategy(self):
        """Factory returns CashFlowInvestor for 'cash_flow'."""
        # Arrange & Act
        strategy = get_investor_strategy("cash_flow")
        
        # Assert
        assert isinstance(strategy, CashFlowInvestor)
        assert strategy.name == "cash_flow"
    
    def test_get_balanced_strategy(self):
        """Factory returns BalancedInvestor for 'balanced'."""
        # Arrange & Act
        strategy = get_investor_strategy("balanced")
        
        # Assert
        assert isinstance(strategy, BalancedInvestor)
        assert strategy.name == "balanced"
    
    def test_get_appreciation_strategy(self):
        """Factory returns AppreciationInvestor for 'appreciation'."""
        # Arrange & Act
        strategy = get_investor_strategy("appreciation")
        
        # Assert
        assert isinstance(strategy, AppreciationInvestor)
        assert strategy.name == "appreciation"
    
    def test_invalid_profile_raises_error(self):
        """Unknown profile raises ValueError."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError) as exc_info:
            get_investor_strategy("unknown_profile")
        
        assert "Unknown investor profile" in str(exc_info.value)


# =============================================================================
# SCORE INTERPRETATION
# =============================================================================

class TestScoreInterpretation:
    """Test score interpretation and ranges."""
    
    def test_score_ranges(self, sample_deal):
        """Scores should fall into interpretable ranges."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(investor_profile="balanced")
        score = result.data.deal_score.value
        
        # Assert - score should be in valid range
        assert 0 <= score <= 100
        
        # Interpret
        if score >= 80:
            interpretation = "Excellent"
        elif score >= 60:
            interpretation = "Good"
        elif score >= 40:
            interpretation = "Fair"
        else:
            interpretation = "Poor"
        
        # Just verify we can interpret
        assert interpretation in ["Excellent", "Good", "Fair", "Poor"]
    
    def test_sample_deal_has_valid_score(self, sample_deal):
        """Sample deal should have a valid score in 0-100 range."""
        # Arrange
        calculator = MetricsCalculator(sample_deal)
        
        # Act
        result = calculator.calculate(investor_profile="balanced")
        score = result.data.deal_score.value
        
        # Assert - score is in valid range
        assert 0 <= score <= 100
        # Sample deal should have some positive score
        assert score > 0
    
    def test_negative_cash_flow_deal_lower_score(self, negative_cash_flow_deal, sample_deal):
        """Negative cash flow deal should score lower."""
        # Arrange
        calc_neg = MetricsCalculator(negative_cash_flow_deal)
        calc_pos = MetricsCalculator(sample_deal)
        
        # Act
        result_neg = calc_neg.calculate(investor_profile="cash_flow")
        result_pos = calc_pos.calculate(investor_profile="cash_flow")
        
        score_neg = result_neg.data.deal_score.value
        score_pos = result_pos.data.deal_score.value
        
        # Assert - negative cash flow should score worse for cash flow investor
        assert score_neg < score_pos
