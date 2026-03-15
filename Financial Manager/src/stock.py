from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Stock:
    """Represents a single stock/quote snapshot.

    Fields are intentionally simple to start and can be extended later.
    """
    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    latest_price: Optional[float] = None
    previous_close: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    timestamp: Optional[datetime] = field(default_factory=datetime.utcnow)

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update fields from a mapping (e.g. API response).

        Accepts keys in snake_case or camelCase commonly returned by APIs.
        """
        # canonical keys we accept
        mapping = {
            'symbol': 'symbol',
            'name': 'name',
            'exchange': 'exchange',
            'latest_price': 'latest_price',
            'last': 'latest_price',
            'price': 'latest_price',
            'previous_close': 'previous_close',
            'prevClose': 'previous_close',
            'volume': 'volume',
            'market_cap': 'market_cap',
            'marketCap': 'market_cap',
            'timestamp': 'timestamp',
        }

        for k, v in data.items():
            key = mapping.get(k, None)
            if key is None:
                # allow direct assign if matches an attribute
                if hasattr(self, k):
                    setattr(self, k, v)
                continue
            if key == 'timestamp' and v is not None:
                # accept ISO strings or epoch
                if isinstance(v, (int, float)):
                    self.timestamp = datetime.utcfromtimestamp(float(v))
                elif isinstance(v, str):
                    try:
                        self.timestamp = datetime.fromisoformat(v)
                    except Exception:
                        # leave as-is
                        pass
                else:
                    self.timestamp = v
            else:
                setattr(self, key, v)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # serialize timestamp to ISO format
        if isinstance(d.get('timestamp'), datetime):
            d['timestamp'] = d['timestamp'].isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Stock':
        ts = data.get('timestamp')
        if isinstance(ts, str):
            try:
                data = dict(data)
                data['timestamp'] = datetime.fromisoformat(ts)
            except Exception:
                pass
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<Stock {self.symbol} {self.latest_price}@{self.timestamp}>"
