# Reports

PyDoover includes utilities for generating reports from channel data, primarily for Excel export.

## Overview

The reports module provides:
- Data retrieval from channels
- Data transformation and flattening
- Excel (XLSX) export
- Custom report generation

## Module Location

```python
from pydoover.reports import Report, XlsxReport
from pydoover.reports.json_flatten import flatten_json
```

## Basic Usage

### Create Report

```python
from pydoover.reports import XlsxReport

report = XlsxReport(
    title="Sensor Data Report",
    filename="sensor_report.xlsx"
)
```

### Add Data

```python
# Add data rows
report.add_row({
    "timestamp": "2024-01-15 10:00:00",
    "temperature": 25.5,
    "humidity": 60,
    "status": "normal"
})

report.add_row({
    "timestamp": "2024-01-15 10:01:00",
    "temperature": 26.0,
    "humidity": 58,
    "status": "normal"
})
```

### Save Report

```python
report.save()
```

## JSON Flattening

Flatten nested JSON for tabular export:

```python
from pydoover.reports.json_flatten import flatten_json

nested = {
    "sensor": {
        "temperature": 25.5,
        "humidity": 60
    },
    "metadata": {
        "location": "Building A",
        "floor": 2
    }
}

flat = flatten_json(nested)
# {
#     "sensor.temperature": 25.5,
#     "sensor.humidity": 60,
#     "metadata.location": "Building A",
#     "metadata.floor": 2
# }
```

## Channel Data Export

### Fetch and Export

```python
from pydoover.cloud.api import Client
from pydoover.reports import XlsxReport
from pydoover.reports.json_flatten import flatten_json
from datetime import datetime, timedelta

def export_channel_data(
    client: Client,
    channel_id: str,
    hours: int = 24
) -> str:
    # Fetch messages
    end = datetime.now()
    start = end - timedelta(hours=hours)

    messages = client.get_channel_messages_in_window(
        channel_id, start, end
    )

    # Create report
    report = XlsxReport(
        title=f"Channel Data Export",
        filename=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

    # Add data
    for msg in messages:
        flat_data = flatten_json(msg.payload)
        flat_data["timestamp"] = msg.timestamp.isoformat()
        report.add_row(flat_data)

    report.save()
    return report.filename
```

## Custom Reports

### Base Report Class

```python
from pydoover.reports.base import Report

class MyReport(Report):
    def __init__(self, title: str):
        super().__init__(title)
        self.data = []

    def add_data(self, data: dict):
        self.data.append(data)

    def generate(self) -> bytes:
        # Custom generation logic
        pass
```

### Excel Report Customization

```python
from pydoover.reports import XlsxReport

class SensorReport(XlsxReport):
    def __init__(self):
        super().__init__(
            title="Daily Sensor Report",
            filename="sensor_report.xlsx"
        )
        self.setup_sheets()

    def setup_sheets(self):
        # Configure worksheets
        self.add_sheet("Temperature")
        self.add_sheet("Humidity")
        self.add_sheet("Summary")

    def add_temperature(self, timestamp, value):
        self.add_row(
            {"timestamp": timestamp, "temperature": value},
            sheet="Temperature"
        )

    def add_humidity(self, timestamp, value):
        self.add_row(
            {"timestamp": timestamp, "humidity": value},
            sheet="Humidity"
        )
```

## Cloud Processor Report

Generate reports in a cloud processor:

```python
from pydoover.cloud.processor import ProcessorBase
from pydoover.reports import XlsxReport
from pydoover.reports.json_flatten import flatten_json
import logging

log = logging.getLogger(__name__)

class ReportGenerator(ProcessorBase):
    def process(self):
        log.info("Generating report")

        # Get data channel
        data_channel = self.fetch_channel_named("sensor_data")
        messages = data_channel.fetch_messages(limit=1000)

        if not messages:
            log.info("No data to report")
            return

        # Create report
        report = XlsxReport(
            title="Automated Sensor Report",
            filename="/tmp/report.xlsx"
        )

        for msg in messages:
            flat = flatten_json(msg.payload)
            flat["timestamp"] = msg.timestamp.isoformat()
            report.add_row(flat)

        report.save()
        log.info(f"Report saved: {report.filename}")

        # Optionally upload or notify
        self.notify_report_ready(report.filename)
```

## Data Transformation

### Aggregation

```python
def aggregate_hourly(messages: list) -> dict:
    """Aggregate messages by hour."""
    hourly = {}

    for msg in messages:
        hour = msg.timestamp.replace(minute=0, second=0, microsecond=0)
        hour_key = hour.isoformat()

        if hour_key not in hourly:
            hourly[hour_key] = {
                "count": 0,
                "sum": 0,
                "min": float("inf"),
                "max": float("-inf")
            }

        value = msg.payload.get("value", 0)
        hourly[hour_key]["count"] += 1
        hourly[hour_key]["sum"] += value
        hourly[hour_key]["min"] = min(hourly[hour_key]["min"], value)
        hourly[hour_key]["max"] = max(hourly[hour_key]["max"], value)

    # Calculate averages
    for hour_key in hourly:
        hourly[hour_key]["avg"] = (
            hourly[hour_key]["sum"] / hourly[hour_key]["count"]
        )

    return hourly
```

### Filtering

```python
def filter_by_range(messages: list, min_val: float, max_val: float) -> list:
    """Filter messages by value range."""
    return [
        msg for msg in messages
        if min_val <= msg.payload.get("value", 0) <= max_val
    ]
```

## Best Practices

1. **Chunk large datasets** - Don't load all data at once
2. **Use streaming** - Write to file incrementally for large reports
3. **Handle missing data** - Default values for missing fields
4. **Include metadata** - Add report generation timestamp, parameters
5. **Validate data** - Check data types before export

## Complete Example

```python
from pydoover.cloud.api import Client
from pydoover.reports import XlsxReport
from pydoover.reports.json_flatten import flatten_json
from datetime import datetime, timedelta
import logging

log = logging.getLogger(__name__)

class DataExporter:
    def __init__(self, client: Client, agent_id: str):
        self.client = client
        self.agent_id = agent_id

    def export_sensor_data(
        self,
        channel_name: str,
        hours: int = 24,
        output_path: str = None
    ) -> str:
        """Export sensor data to Excel."""

        # Get channel
        channel = self.client.get_channel_named(channel_name, self.agent_id)

        # Fetch messages
        end = datetime.now()
        start = end - timedelta(hours=hours)

        log.info(f"Fetching data from {start} to {end}")
        messages = self.client.get_channel_messages_in_window(
            channel.id, start, end
        )

        if not messages:
            log.warning("No messages found")
            return None

        log.info(f"Found {len(messages)} messages")

        # Create report
        if output_path is None:
            output_path = f"export_{channel_name}_{datetime.now():%Y%m%d_%H%M%S}.xlsx"

        report = XlsxReport(
            title=f"{channel_name} Export",
            filename=output_path
        )

        # Process messages
        for msg in messages:
            row = flatten_json(msg.payload)
            row["_timestamp"] = msg.timestamp.isoformat()
            row["_message_id"] = msg.id
            report.add_row(row)

        # Add summary sheet
        self._add_summary(report, messages)

        report.save()
        log.info(f"Report saved to {output_path}")

        return output_path

    def _add_summary(self, report: XlsxReport, messages: list):
        """Add summary statistics."""
        if not messages:
            return

        # Calculate statistics
        values = [
            m.payload.get("value", 0)
            for m in messages
            if "value" in m.payload
        ]

        if values:
            summary = {
                "total_messages": len(messages),
                "value_count": len(values),
                "value_min": min(values),
                "value_max": max(values),
                "value_avg": sum(values) / len(values),
                "start_time": messages[-1].timestamp.isoformat(),
                "end_time": messages[0].timestamp.isoformat()
            }

            # Add to summary sheet if supported
            # report.add_row(summary, sheet="Summary")


# Usage
if __name__ == "__main__":
    client = Client(config_profile="default")
    exporter = DataExporter(client, client.agent_id)

    filepath = exporter.export_sensor_data(
        "sensor_data",
        hours=24
    )

    print(f"Export complete: {filepath}")
```

---

> [!warning] Implementation Notes
> The exact API for report generation may vary. Consult the current pydoover source for the latest implementation details.

See Also:
- [[40-Cloud-API|Cloud API]]
- [[42-Channels-and-Messages|Channels and Messages]]
- [[60-Utilities|Utilities Overview]]

#reports #export #excel #data #pydoover
