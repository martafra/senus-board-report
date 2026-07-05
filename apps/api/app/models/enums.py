import enum


class PeriodType(str, enum.Enum):
    ANNUAL = "ANNUAL"
    HALF_YEAR = "HALF_YEAR"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"


class Provenance(str, enum.Enum):
    # REPORTED = pulled verbatim from a source filing
    # MODELLED = derived under a disclosed assumption (seasonality split, EBITDA proxy, etc.)
    REPORTED = "REPORTED"
    MODELLED = "MODELLED"


class CustomerChannel(str, enum.Enum):
    ENTERPRISE = "ENTERPRISE"
    INDEPENDENT = "INDEPENDENT"
    RD = "RD"


class UserRole(str, enum.Enum):
    CEO = "CEO"
    BOARD = "BOARD"
    INVESTOR = "INVESTOR"
    CREDIT_PROVIDER = "CREDIT_PROVIDER"
    ADMIN = "ADMIN"
