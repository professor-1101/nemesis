"""Configuration schemas for validation."""

PLAYWRIGHT_SCHEMA = {
    "required": ["browser"],
    "fields": {
        "browser": {
            "type": "dict",
            "fields": {
                "type": {
                    "type": "string",
                    "enum": ["chromium", "firefox", "webkit"],
                },
                "headless": {
                    "type": "boolean",
                },
                "slow_mo": {
                    "type": "integer",
                    "min": 0,
                },
            },
        },
        "viewport": {
            "type": "dict",
            "fields": {
                "width": {
                    "type": "integer",
                    "min": 320,
                },
                "height": {
                    "type": "integer",
                    "min": 240,
                },
            },
        },
        "timeouts": {
            "type": "dict",
            "fields": {
                "default": {
                    "type": "integer",
                    "min": 1000,
                },
                "navigation": {
                    "type": "integer",
                    "min": 1000,
                },
            },
        },
    },
}

REPORTPORTAL_SCHEMA = {
    "required": ["endpoint", "project", "api_key"],
    "fields": {
        "endpoint": {
            "type": "string",
        },
        "project": {
            "type": "string",
        },
        "api_key": {
            "type": "string",
        },
        "launch_name": {
            "type": "string",
        },
        "client_type": {
            "type": "string",
            "enum": ["SYNC", "ASYNC"],
        },
    },
}

BEHAVE_SCHEMA = {
    "fields": {
        "behave": {
            "type": "dict",
            "fields": {
                "paths": {
                    "type": "string",
                },
                "format": {
                    "type": "string",
                },
            },
        },
        "userdata": {
            "type": "dict",
        },
    },
}

LOGGING_SCHEMA = {
    "fields": {
        "level": {
            "type": "string",
            "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        },
        "format": {
            "type": "string",
            "enum": ["json", "structured", "simple"],
        },
        "console": {
            "type": "dict",
        },
        "file": {
            "type": "dict",
        },
    },
}

REPORTING_SCHEMA = {
    "fields": {
        "mode": {
            "type": "string",
            "enum": ["local", "reportportal", "all"],
        },
        "local": {
            "type": "dict",
            "fields": {
                "enabled": {
                    "type": "boolean",
                },
                "format": {
                    "type": "string",
                },
            },
        },
        "reportportal": {
            "type": "dict",
            "fields": {
                "enabled": {
                    "type": "boolean",
                },
            },
        },
    },
}

ATTACHMENTS_SCHEMA = {
    "fields": {
        "screenshots": {
            "type": "dict",
            "fields": {
                "enabled": {"type": "boolean"},
                "format": {"type": "string", "enum": ["png", "jpg", "jpeg"]},
                "quality": {"type": "integer", "min": 1, "max": 100},
            },
        },
        "videos": {
            "type": "dict",
            "fields": {
                "enabled": {"type": "boolean"},
                "format": {"type": "string", "enum": ["webm", "mp4", "avi"]},
                "quality": {"type": "string", "enum": ["low", "medium", "high"]},
            },
        },
        "traces": {
            "type": "dict",
            "fields": {
                "enabled": {"type": "boolean"},
                "format": {"type": "string", "enum": ["zip", "json"]},
                "include_sources": {"type": "boolean"},
            },
        },
        "network": {
            "type": "dict",
            "fields": {
                "enabled": {"type": "boolean"},
                "format": {"type": "string", "enum": ["har", "json"]},
                "include_responses": {"type": "boolean"},
            },
        },
        "performance": {
            "type": "dict",
            "fields": {
                "enabled": {"type": "boolean"},
                "format": {"type": "string", "enum": ["json", "csv"]},
                "metrics": {"type": "array"},
            },
        },
        "console": {
            "type": "dict",
            "fields": {
                "enabled": {"type": "boolean"},
                "format": {"type": "string", "enum": ["jsonl", "txt", "json"]},
                "levels": {"type": "array"},
            },
        },
    },
}
