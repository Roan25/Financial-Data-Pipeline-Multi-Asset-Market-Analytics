from enum import Enum
from pydantic import BaseModel, Field, model_validator, computed_field
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
import pandas as pd

# ... [Skipping the middle classes as we only need to update the top imports and bottom class]

class OptionType(str, Enum):
    CE = "CE"
    PE = "PE"

class MarketPhase(str, Enum):
    LONG_BUILDUP = "Long Buildup"
    SHORT_BUILDUP = "Short Buildup"
    LONG_UNWINDING = "Long Unwinding"
    SHORT_COVERING = "Short Covering"
    NEUTRAL = "Neutral"

class EquityConstituentRecord(BaseModel):
    symbol: str
    sector: str
    market_cap: float = Field(gt=0)
    current_price: float = Field(gt=0)
    pct_change: float
    volume: int

    @model_validator(mode='after')
    def check_circuit_breaker(self):
        if abs(self.pct_change) > 7.0:
            raise ValueError(f"Circuit breaker violation: {self.pct_change}% for {self.symbol}")
        return self

class OptionContractRecord(BaseModel):
    strike_price: float = Field(gt=0)
    option_type: OptionType
    expiry_date: str
    underlying_value: float
    ltp: float
    price_change: float
    open_interest: int = Field(ge=0)
    change_in_oi: int
    traded_volume: int = Field(ge=0)
    implied_volatility: float

    @model_validator(mode='after')
    def check_strike_interval(self):
        if self.strike_price % 50 != 0:
            raise ValueError(f"Strike price {self.strike_price} is not a multiple of 50.")
        return self

    @computed_field
    @property
    def market_phase(self) -> str:
        if self.price_change > 0 and self.change_in_oi > 0:
            return MarketPhase.LONG_BUILDUP.value
        elif self.price_change < 0 and self.change_in_oi > 0:
            return MarketPhase.SHORT_BUILDUP.value
        elif self.price_change < 0 and self.change_in_oi < 0:
            return MarketPhase.LONG_UNWINDING.value
        elif self.price_change > 0 and self.change_in_oi < 0:
            return MarketPhase.SHORT_COVERING.value
        return MarketPhase.NEUTRAL.value

class MacroRateRecord(BaseModel):
    instrument: str
    yield_rate: float = Field(ge=0, le=25)
    daily_bps_change: float
    as_of_date: str

class DataQualityGate:
    @staticmethod
    def validate_batch(data: List[Dict[Any, Any]], model: BaseModel) -> Tuple[pd.DataFrame, List[Dict[Any, Any]]]:
        clean = []
        rejected = []
        for row in data:
            try:
                valid_record = model.model_validate(row)
                clean.append(valid_record.model_dump())
            except Exception as e:
                rejected.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "reason": str(e),
                    "payload": row
                })
        return pd.DataFrame(clean), rejected

    @staticmethod
    def validate_equity_batch(data: List[Dict]) -> Tuple[pd.DataFrame, List[Dict]]:
        return DataQualityGate.validate_batch(data, EquityConstituentRecord)

    @staticmethod
    def validate_option_chain_batch(data: List[Dict]) -> Tuple[pd.DataFrame, List[Dict]]:
        return DataQualityGate.validate_batch(data, OptionContractRecord)
