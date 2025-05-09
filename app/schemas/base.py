from pydantic import ConfigDict
from datetime import datetime, date

BaseModelConfig = ConfigDict(
    from_attributes=True,
    json_encoders={
        datetime: lambda dt: dt.isoformat(),
        date:     lambda d:  d.isoformat(),
    },
)
