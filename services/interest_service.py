"""
Interest Calculation Service for Jewelry Mortgage.
Supports any custom/random interest rates, monthly calculation based on principal and jewel weight,
and redemption settlement calculation without forcing rigid defaults.
"""
from datetime import datetime, date
import math

class InterestService:
    @staticmethod
    def get_default_rate(jewel_type=None):
        """Returns empty string so no default rate is forced."""
        return ""

    @staticmethod
    def calculate_monthly_interest(principal, rate_pct, net_weight=0, jewel_type=""):
        """
        Calculates monthly interest amount based on user-entered principal and custom rate.
        Returns:
            monthly_interest: float
            per_gram_monthly: float
            annual_rate_pct: float
        """
        try:
            p = float(principal) if principal else 0.0
            r = float(rate_pct) if rate_pct else 0.0
            w = float(net_weight) if net_weight else 0.0

            # Monthly interest on principal amount
            monthly_interest = round(p * (r / 100.0), 2)

            # Per gram interest rate representation
            per_gram_monthly = round(monthly_interest / w, 2) if w > 0 else 0.0

            return {
                "monthly_interest": monthly_interest,
                "per_gram_monthly": per_gram_monthly,
                "annual_rate_pct": round(r * 12, 2)
            }
        except Exception:
            return {"monthly_interest": 0.0, "per_gram_monthly": 0.0, "annual_rate_pct": 0.0}

    @staticmethod
    def calculate_settlement(pledge_date_str, release_date_str, principal, rate_pct, discount=0.0, min_one_month=True):
        """
        Calculates redemption settlement:
        - Exact days elapsed
        - Months elapsed
        - Accrued interest
        - Total settlement amount
        """
        try:
            # Parse dates
            p_date = datetime.strptime(pledge_date_str.strip(), "%Y-%m-%d").date()
            if isinstance(release_date_str, str) and release_date_str.strip():
                r_date = datetime.strptime(release_date_str.strip(), "%Y-%m-%d").date()
            elif isinstance(release_date_str, date):
                r_date = release_date_str
            else:
                r_date = date.today()

            p = float(principal) if principal else 0.0
            r = float(rate_pct) if rate_pct else 0.0
            disc = float(discount) if discount else 0.0

            days = (r_date - p_date).days
            if days < 0:
                days = 0

            # Monthly & daily interest calculation
            monthly_interest = round(p * (r / 100.0), 2)
            daily_interest = monthly_interest / 30.0

            if min_one_month and days <= 30:
                months_billed = 1.0
                accrued_interest = monthly_interest
            else:
                months_billed = round(days / 30.0, 2)
                accrued_interest = round(daily_interest * days, 2)

            total_before_disc = round(p + accrued_interest, 2)
            net_payable = max(0.0, round(total_before_disc - disc, 2))

            return {
                "days_elapsed": days,
                "months_billed": months_billed,
                "monthly_interest": monthly_interest,
                "daily_interest": round(daily_interest, 2),
                "accrued_interest": accrued_interest,
                "principal": p,
                "discount": disc,
                "net_payable": net_payable
            }
        except Exception as e:
            print(f"Settlement calculation error: {e}")
            p_val = float(principal) if principal else 0.0
            return {
                "days_elapsed": 0,
                "months_billed": 1.0,
                "monthly_interest": 0.0,
                "daily_interest": 0.0,
                "accrued_interest": 0.0,
                "principal": p_val,
                "discount": 0.0,
                "net_payable": p_val
            }
