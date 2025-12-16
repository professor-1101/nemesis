"""Performance metrics data models."""
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class NavigationTiming:
    """Navigation timing metrics."""
    fetch_start: float = 0
    domain_lookup_start: float = 0
    domain_lookup_end: float = 0
    connect_start: float = 0
    connect_end: float = 0
    secure_connection_start: float = 0
    request_start: float = 0
    response_start: float = 0
    response_end: float = 0
    dom_interactive: float = 0
    dom_content_loaded_start: float = 0
    dom_content_loaded_end: float = 0
    dom_complete: float = 0
    load_event_start: float = 0
    load_event_end: float = 0
    transfer_size: int = 0
    encoded_body_size: int = 0
    decoded_body_size: int = 0
    redirect_count: int = 0
    type: str = ""

    # Calculated metrics
    dns_time: float = 0
    tcp_time: float = 0
    ttfb: float = 0  # Time to First Byte
    download_time: float = 0
    dom_processing_time: float = 0
    total_load_time: float = 0


@dataclass
class ResourceTiming:
    """Individual resource timing."""
    name: str
    duration: float
    transfer_size: int
    encoded_body_size: int
    decoded_body_size: int
    initiator_type: str
    start_time: float
    response_end: float
    fetch_start: float
    domain_lookup_start: float = 0
    domain_lookup_end: float = 0
    connect_start: float = 0
    connect_end: float = 0
    request_start: float = 0
    response_start: float = 0
    cache_hit: bool = False


@dataclass
class PaintTiming:
    """Paint timing metrics."""
    first_paint: float = 0  # FP
    first_contentful_paint: float = 0  # FCP


@dataclass
class WebVitals:
    """Core Web Vitals and related metrics."""
    # Core Web Vitals
    lcp: float = 0  # Largest Contentful Paint
    inp: float = 0  # Interaction to Next Paint
    cls: float = 0  # Cumulative Layout Shift

    # Additional vitals
    fcp: float = 0  # First Contentful Paint
    tti: float = 0  # Time to Interactive
    tbt: float = 0  # Total Blocking Time
    fid: float = 0  # First Input Delay (legacy)

    # Status (good/needs-improvement/poor)
    lcp_status: str = ""
    inp_status: str = ""
    cls_status: str = ""


@dataclass
class MemoryMetrics:
    """Memory usage metrics (Chrome-specific)."""
    used_js_heap_size: int = 0
    total_js_heap_size: int = 0
    js_heap_size_limit: int = 0
    used_js_heap_size_mb: float = 0
    total_js_heap_size_mb: float = 0
    heap_usage_percent: float = 0


@dataclass
class RuntimeMetrics:
    """Runtime performance metrics."""
    fps: float = 0  # Frames per second
    dropped_frames: int = 0
    total_frames: int = 0
    jank_count: int = 0  # Frames > 50ms
    average_frame_time: float = 0
    longest_frame: float = 0


@dataclass
class LongTask:
    """Long task entry (>= 50ms)."""
    name: str
    duration: float
    start_time: float
    attribution: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class LayoutShift:
    """Layout shift entry."""
    value: float
    start_time: float
    had_recent_input: bool
    sources: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class UserTimingEntry:
    """User timing mark or measure."""
    name: str
    entry_type: str  # 'mark' or 'measure'
    start_time: float
    duration: float = 0


@dataclass
class EventTiming:
    """Event timing entry (for interactions)."""
    name: str  # e.g., 'click', 'keydown'
    duration: float
    processing_start: float
    processing_end: float
    start_time: float
    cancelable: bool = False
    target: str = ""


@dataclass
class ResourceSummary:
    """Summary of resources by type."""
    total_count: int = 0
    total_transfer_size: int = 0
    total_encoded_size: int = 0
    total_decoded_size: int = 0
    total_duration: float = 0
    by_type: dict[str, dict[str, Any]] = field(default_factory=dict)
    cache_hit_ratio: float = 0
    largest_resources: list[ResourceTiming] = field(default_factory=list)


@dataclass
class PerformanceReport:
    """Complete performance report containing all metrics."""
    navigation: NavigationTiming | None = None
    resources: list[ResourceTiming] = field(default_factory=list)
    paint: PaintTiming | None = None
    web_vitals: WebVitals | None = None
    memory: MemoryMetrics | None = None
    runtime: RuntimeMetrics | None = None
    long_tasks: list[LongTask] = field(default_factory=list)
    layout_shifts: list[LayoutShift] = field(default_factory=list)
    user_timing: list[UserTimingEntry] = field(default_factory=list)
    event_timing: list[EventTiming] = field(default_factory=list)

    # Summary
    resource_summary: ResourceSummary = field(default_factory=ResourceSummary)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)
