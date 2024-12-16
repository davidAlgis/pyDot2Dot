DEFAULT_CONFIG_CONTENT = {
    "input": "input.png",
    "output": None,
    "shapeDetection": "Automatic",
    "distance": ["", ""],
    "font": "Arial.ttf",
    "fontSize": "57",
    "fontColor": [0, 0, 0, 255],
    "dotColor": [0, 0, 0, 255],
    "radius": "10",
    "dpi": 400,
    "epsilon": 15,
    "debug": False,
    "displayOutput": True,
    "verbose": True,
    "thresholdBinary": [100, 255],
    "gui": True
}

CONFIG_SCHEMA = {
    "type":
    "object",
    "properties": {
        "input": {
            "type": "string"
        },
        "output": {
            "type": ["string", "null"]
        },
        "shapeDetection": {
            "type": "string",
            "enum": ["Automatic", "Contour", "Path"]
        },
        "distance": {
            "type": "array",
            "items": {
                "type": ["string", "null"]
            },
            "minItems": 2,
            "maxItems": 2,
        },
        "font": {
            "type": "string"
        },
        "fontSize": {
            "type": "string"
        },
        "fontColor": {
            "type": "array",
            "items": {
                "type": "integer",
                "minimum": 0,
                "maximum": 255
            },
            "minItems": 4,
            "maxItems": 4,
        },
        "dotColor": {
            "type": "array",
            "items": {
                "type": "integer",
                "minimum": 0,
                "maximum": 255
            },
            "minItems": 4,
            "maxItems": 4,
        },
        "radius": {
            "type": "string"
        },
        "dpi": {
            "type": "integer",
            "minimum": 1
        },
        "epsilon": {
            "type": "integer",
            "minimum": 0
        },
        "debug": {
            "type": "boolean"
        },
        "displayOutput": {
            "type": "boolean"
        },
        "verbose": {
            "type": "boolean"
        },
        "thresholdBinary": {
            "type": "array",
            "items": {
                "type": "integer",
                "minimum": 0,
                "maximum": 255
            },
            "minItems": 2,
            "maxItems": 2,
        },
        "gui": {
            "type": "boolean"
        },
    },
    "required": [
        "input",
        "shapeDetection",
        "distance",
        "font",
        "fontSize",
        "fontColor",
        "dotColor",
        "radius",
        "dpi",
        "epsilon",
        "debug",
        "displayOutput",
        "verbose",
        "thresholdBinary",
        "gui",
    ],
    "additionalProperties":
    False,
}