# ADP Protocol Technical Documentation

This technical documentation provides detailed guidance on using ADP (AI-Driven Programming) in various scenarios, covering implementation details, best practices, and advanced use cases.

## Table of Contents

- [Installation](#installation)
- [Core Concepts](#core-concepts)
- [Using ADP in Various Scenarios](#using-adp-in-various-scenarios)
  - [Single File Documentation](#single-file-documentation)
  - [Documenting Classes and Functions](#documenting-classes-and-functions)
  - [Capturing Domain Knowledge](#capturing-domain-knowledge)
  - [Expressing Technical Constraints](#expressing-technical-constraints)
  - [Team and Ownership Metadata](#team-and-ownership-metadata)
- [Language-Specific Implementations](#language-specific-implementations)
- [Integration Patterns](#integration-patterns)
  - [IDE Integration](#ide-integration)
  - [CI/CD Integration](#cicd-integration)
  - [Documentation Generation](#documentation-generation)
- [Working with the CLI](#working-with-the-cli)
- [Knowledge Graph Usage](#knowledge-graph-usage)
- [Schema Reference](#schema-reference)

## Installation

### From PyPI

```bash
pip install adp-py
```

### From Source

```bash
git clone https://github.com/mkpvishnu/adpp.git
cd adpp
pip install -e .
```

### Dependencies

ADP requires the following dependencies, which are automatically installed:
- Python 3.7+
- pyyaml
- jsonschema
- click
- rich
- graphviz
- networkx
- matplotlib

## Core Concepts

ADP operates on four fundamental concepts:

1. **Metadata Blocks**: JSON structures embedded in code comments that follow a standardized schema
2. **Parsers**: Language-specific components that extract metadata from code files
3. **Knowledge Graph**: A connected representation of code components and their relationships
4. **Validators**: Tools that ensure metadata accuracy and consistency

### Metadata Block Structure

Metadata blocks are embedded in code comments using the `@ai-metadata` marker:

```python
"""
@ai-metadata {
    "domain": "authentication",
    "description": "JWT token validation middleware",
    "dependencies": ["auth_service.py", "rate_limiter.py"],
    "performance": [
        {
            "consideration": "Token validation is CPU-intensive",
            "mitigation": "Results are cached with 5-minute TTL"
        }
    ],
    "dataHandling": [
        {
            "dataType": "PII",
            "handling": "Encrypted in transit and at rest"
        }
    ]
}
"""
```

### Metadata Scopes

ADP supports metadata at multiple scopes:

- **File**: Applied to the entire file
- **Class**: Describes a class/interface
- **Function/Method**: Describes a function or method
- **Variable/Constant**: Describes important variables or constants
- **Block**: Describes a specific code block

## Using ADP in Various Scenarios

### Single File Documentation

When documenting a single file, place a metadata block at the top of the file:

```python
# auth_service.py
"""
@ai-metadata {
    "domain": "authentication",
    "description": "Service for user authentication and authorization",
    "dependencies": ["database.py", "user_model.py"],
    "team": "security",
    "securityConsiderations": [
        {
            "concern": "Password storage",
            "solution": "Argon2id hashing with per-user salt"
        }
    ]
}
"""
import hashlib
import secrets
from database import DatabaseConnection
# Rest of implementation...
```

### Documenting Classes and Functions

For class-level and function-level metadata:

```python
class UserAuthenticator:
    """
    @ai-metadata {
        "domain": "authentication",
        "description": "Handles user authentication against various backends",
        "dependencies": ["DatabaseConnection", "UserRepository"]
    }
    """
    
    def authenticate(self, username, password):
        """
        @ai-metadata {
            "description": "Authenticates a user against stored credentials",
            "performance": [
                {
                    "consideration": "Should complete within 100ms",
                    "explanation": "Used in the login flow critical path"
                }
            ],
            "inputs": [
                {"name": "username", "description": "User identifier (email or username)"},
                {"name": "password", "description": "Plaintext password (will be hashed)"}
            ],
            "outputs": [
                {"name": "success", "type": "boolean", "description": "Whether authentication succeeded"},
                {"name": "user", "type": "User|None", "description": "User object if successful, None otherwise"}
            ]
        }
        """
        # Implementation...
```

### Capturing Domain Knowledge

Use the `domain` field to group related components:

```python
"""
@ai-metadata {
    "domain": "payment-processing",
    "subdomains": ["credit-card", "refunds"],
    "description": "Processes credit card payments and refunds",
    "businessRules": [
        "Refunds can only be processed within 90 days of purchase",
        "Failed payments should be retried up to 3 times with exponential backoff"
    ]
}
"""
```

### Expressing Technical Constraints

Document performance, scaling, and technical constraints:

```python
"""
@ai-metadata {
    "description": "High-throughput order processor",
    "performance": [
        {
            "metric": "Throughput",
            "expectation": "1000 orders/second sustained",
            "degradationBehavior": "Graceful degradation by queuing orders"
        },
        {
            "metric": "Latency",
            "expectation": "p99 < 200ms",
            "degradationBehavior": "Alert when p99 > 150ms"
        }
    ],
    "scaling": {
        "strategy": "Horizontal",
        "bottlenecks": ["Database connections", "Redis cache size"],
        "recommendations": ["Increase connection pool during peak hours"]
    }
}
"""
```

### Team and Ownership Metadata

Track ownership and team responsibility:

```python
"""
@ai-metadata {
    "description": "Customer communication service",
    "team": "customer-engagement",
    "pointOfContact": "sarah.chen@company.com",
    "slackChannel": "#team-customer-comms",
    "ticketingLabel": "customer-communication-service",
    "onCall": {
        "rotation": "Team CE Rotation",
        "escalationPath": ["primary-on-call", "team-lead", "director"]
    }
}
"""
```

## Language-Specific Implementations

### Python

In Python, metadata blocks are embedded in docstrings:

```python
"""
@ai-metadata {
    "domain": "data-processing",
    "description": "Data transformation pipeline"
}
"""
```

### JavaScript/TypeScript

In JavaScript/TypeScript, use block comments:

```javascript
/**
 * @ai-metadata {
 *     "domain": "frontend",
 *     "description": "User authentication component",
 *     "dependencies": ["AuthService", "UserStore"]
 * }
 */
```

### Java

In Java, use Javadoc comments:

```java
/**
 * @ai-metadata {
 *     "domain": "order-management",
 *     "description": "Order processing service",
 *     "dependencies": ["InventoryService", "PaymentService"]
 * }
 */
public class OrderService {
    // Implementation...
}
```

### Go

In Go, use standard comments:

```go
// @ai-metadata {
//     "domain": "api-gateway",
//     "description": "Authentication middleware",
//     "dependencies": ["jwt-service", "user-service"]
// }
```

## Integration Patterns (Yet to be implemented)
#### Below will give a good Idea on how easy different integrations will look like

### IDE Integration

#### VS Code Extension

1. Install the ADP VS Code extension
2. Configure settings in `.vscode/settings.json`:

```json
{
    "adp.enableValidation": true,
    "adp.validateOnSave": true,
    "adp.schemaPath": "./schemas/adp-schema.json",
    "adp.highlightMetadataBlocks": true
}
```

#### JetBrains IDEs (IntelliJ, PyCharm, etc.)

1. Install the ADP Plugin from the JetBrains Marketplace
2. Configure in Settings → Languages & Frameworks → ADP

### CI/CD Integration

Add metadata validation to your CI pipeline:

#### GitHub Actions

```yaml
name: Validate ADP Metadata

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: pip install adp-py
    - name: Validate metadata
      run: python -m adp_py.cli.cli validate ./src
```

#### Jenkins

```groovy
pipeline {
    agent any
    stages {
        stage('Validate ADP Metadata') {
            steps {
                sh 'pip install adp-py'
                sh 'python -m adp_py.cli.cli validate ./src'
            }
        }
    }
}
```

### Documentation Generation (Yet to be implemented)

Generate static documentation from metadata:

```bash
# Generate HTML documentation
python -m adp_py.cli.cli generate-docs --format html --output docs/adp-metadata

# Generate Markdown documentation
python -m adp_py.cli.cli generate-docs --format markdown --output docs/adp-metadata.md
```

## Working with the CLI

### Available Commands

| Command | Description |
|---------|-------------|
| `scan` | Scan files/directories to extract metadata |
| `validate` | Validate metadata against schema |
| `visualize` | Generate a knowledge graph visualization |
| `show` | Display metadata for specific files |
| `statistics` | Generate statistics about metadata usage |
| `export` | Export metadata to various formats |
| `import` | Import metadata from external sources |
| `generate-docs` | Generate documentation from metadata |

### Command Examples

#### Scan Directory

```bash
# Basic scanning
python -m adp_py.cli.cli scan ./src

# Scan with specific file extensions
python -m adp_py.cli.cli scan ./src --extensions py,ts,js

# Exclude directories
python -m adp_py.cli.cli scan ./src --exclude node_modules,__pycache__

# Output to JSON file
python -m adp_py.cli.cli scan ./src --output metadata-inventory.json
```

#### Validate Metadata

```bash
# Validate all metadata in a directory
python -m adp_py.cli.cli validate ./src

# Validate with custom schema
python -m adp_py.cli.cli validate ./src --schema ./schemas/custom-schema.json

# Strict validation (fail on warnings)
python -m adp_py.cli.cli validate ./src --strict

# Generate validation report
python -m adp_py.cli.cli validate ./src --report validation-report.json
```

#### Generate Visualizations

```bash
# Basic knowledge graph
python -m adp_py.cli.cli visualize ./src --output knowledge-graph.png

# Focus on specific domain
python -m adp_py.cli.cli visualize ./src --domain payment-processing --output payment-domain.png

# Change layout algorithm
python -m adp_py.cli.cli visualize ./src --layout fdp --output graph-fdp.png

# Export to different formats
python -m adp_py.cli.cli visualize ./src --format svg --output knowledge-graph.svg
```

#### Export Metadata

```bash
# Export to JSON
python -m adp_py.cli.cli export ./src --format json --output metadata.json

# Export to CSV (for spreadsheet analysis)
python -m adp_py.cli.cli export ./src --format csv --output metadata.csv

# Export specific domains
python -m adp_py.cli.cli export ./src --domains auth,payment --format json --output selected-domains.json
```

## Knowledge Graph Usage

### Analyzing Dependencies

To analyze dependencies between components:

```bash
# Generate dependency graph
python -m adp_py.cli.cli visualize ./src --relationship-types dependency --output dependencies.png

# Find circular dependencies
python -m adp_py.cli.cli analyze-dependencies ./src --find-circular

# List all dependencies for a specific file
python -m adp_py.cli.cli analyze-dependencies ./src/auth_service.py --depth 2
```

### Domain Analysis

To analyze and visualize domain boundaries:

```bash
# List all domains
python -m adp_py.cli.cli list-domains ./src

# Generate domain-centric graph
python -m adp_py.cli.cli visualize ./src --group-by domain --output domain-graph.png

# Analyze cross-domain dependencies
python -m adp_py.cli.cli analyze-domains ./src --cross-domain-dependencies
```

## Schema Reference

### Core Schema Fields

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string | Business/technical domain the component belongs to |
| `description` | string | Human-readable description of the component |
| `dependencies` | string[] | List of components this component depends on |
| `team` | string | Team responsible for the component |
| `performance` | object[] | Performance considerations and constraints |
| `dataHandling` | object[] | Data handling and privacy considerations |
| `businessRules` | string[] | Business rules implemented by the component |
| `securityConsiderations` | object[] | Security considerations |

### Extended Schema Fields

| Field | Type | Description |
|-------|------|-------------|
| `apis` | object[] | API definitions exposed by the component |
| `events` | object[] | Events produced or consumed |
| `resources` | object[] | Resources used (databases, queues, etc.) |
| `architecture` | object | Architectural patterns implemented |
| `testing` | object | Testing strategies and considerations |
| `deployment` | object | Deployment requirements and considerations |
| `monitoring` | object | Monitoring and observability |
| `cost` | object | Cost considerations |
