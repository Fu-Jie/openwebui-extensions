# Plugins

English | [中文](./README_CN.md)

This directory contains four types of plugins for OpenWebUI:

- **Filters**: Process user input before sending to LLM
- **Actions**: Trigger custom functionalities from chat
- **Pipes**: Enhance LLM responses before displaying to user
- **Tools**: Provide callable utility functions for models in Workspace > Tools

## 📦 Plugin Types Overview

### 🔧 Filters (`/filters`)

Filters modify user input before it reaches the LLM. They are useful for:

- Input validation and normalization
- Adding system prompts or context
- Compressing long conversations
- Preprocessing and formatting

[View Filters →](./filters/README.md)

### 🎬 Actions (`/actions`)

Actions are custom functionalities triggered from chat. They are useful for:

- Generating outputs (mind maps, charts, etc.)
- Interacting with external APIs
- Data transformations
- File operations and exports
- Complex workflows

[View Actions →](./actions/README.md)

### 📤 Pipes (`/pipes`)

Pipes process LLM responses after generation. They are useful for:

- Response formatting
- Content enhancement
- Translation and transformation
- Response filtering
- Integration with external services

[View Pipes →](./pipes/README.md)

### 🧰 Tools (`/tools`)

Tools are callable utilities enabled in **Workspace > Tools**. They are useful for:

- Data lookups and utility operations
- Structured function-style actions
- Lightweight model-agnostic capabilities

[View Tools →](./tools/README.md)

## 🚀 Quick Start

### Installing Plugins

1. **Download** the desired plugin file (`.py`)
2. **Open** OpenWebUI Admin Settings → Plugins
3. **Select** the plugin type (Filters, Actions, or Pipes)
4. **Upload** the file
5. **Refresh** the page
6. **Configure** in chat settings

### Using Plugins

- **Filters**: Automatically applied to all inputs when enabled
- **Actions**: Selected manually from the actions menu during chat
- **Pipes**: Automatically applied to all responses when enabled

## 📚 Plugin Documentation

Each plugin directory contains:

- Plugin code (`.py` files)
- English documentation (`README.md`)
- Chinese documentation (`README_CN.md`)
- Configuration and usage guides

## 🛠️ Plugin Development

To create a new plugin:

1. Choose the plugin type (Filter, Action, or Pipe)
2. Navigate to the corresponding directory
3. Create a new folder for your plugin
4. Write the plugin code with clear documentation
5. Create `README.md` and `README_CN.md`
6. Update the main README in that directory

### Plugin Structure Template

```python
plugins/
├── filters/
│   ├── my_filter/
│   │   ├── my_filter.py          # Plugin code
│   │   ├── my_filter_cn.py       # Optional: Chinese version
│   │   ├── README.md              # Documentation
│   │   └── README_CN.md           # Chinese documentation
│   └── README.md
├── actions/
│   ├── my_action/
│   │   ├── my_action.py
│   │   ├── README.md
│   │   └── README_CN.md
│   └── README.md
└── pipes/
    ├── my_pipe/
    │   ├── my_pipe.py
    │   ├── README.md
    │   └── README_CN.md
    └── README.md
```

## 📋 Documentation Checklist

Each plugin should include:

- [ ] Clear feature description
- [ ] Configuration parameters with defaults
- [ ] Installation and setup instructions
- [ ] Usage examples
- [ ] Troubleshooting guide
- [ ] Performance considerations
- [ ] Version and author information

## Author

Fu-Jie
GitHub: [Fu-Jie/openwebui-extensions](https://github.com/Fu-Jie/openwebui-extensions)

---

> **Note**: For detailed information about each plugin type, see the respective README files in each plugin type directory.
