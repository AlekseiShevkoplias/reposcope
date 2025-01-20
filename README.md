# RepoScope

[![PyPI version](https://badge.fury.io/py/reposcope.svg)](https://pypi.org/project/reposcope/)
[![GitHub](https://img.shields.io/github/license/AlekseiShevkoplias/reposcope)](https://github.com/AlekseiShevkoplias/reposcope/blob/main/LICENSE)

# RepoScope

RepoScope is a command-line tool designed to simplify the process of sharing repository contents, especially when working with AI assistants or code review platforms. It helps to quickly and easily share the entire context of a code project without manually copying and pasting individual files.
It also allows user to define the content of which files they want to see in the generated output file with flexible pattern matching.

## Quickstart

Install with pip:
```bash
pip install reposcope
```

### Basic Usage

Create a snapshot of your repository:
```bash
# In your project directory, run:
reposcope

# This creates context.txt with all your files
```

Choose which files to include:
```bash
# Only share Python source files
reposcope -i "*.py"

# Only share files from src directory and documentation
reposcope -i "src/*" "*.md"
```

Skip unwanted files:
```bash
# Skip log files and build directory
reposcope -x "*.log" "build/"

# Use your existing .gitignore file
reposcope -g   # This skips the same files that git ignores
```

Save your preferred patterns for reuse:
```bash
# Create a profile for source code reviews
reposcope profile create source --mode include
reposcope profile add source "src/*.py" "tests/*.py" "*.md"

# Use it later
reposcope -p source
```

### Output Format

RepoScope generates a context.txt file that looks like this:
```
Repository: my-project

File Tree:
└── src/main.py
└── src/utils.py
└── README.md

File Contents:

--- src/main.py ---
def main():
    print("Hello World!")
...
```

## Command Line Options

| Short | Long                 | Description                         |
|-------|----------------------|-------------------------------------|
| -g    | --use-gitignore     | Use .gitignore from current dir     |
| -x    | --exclude           | Exclude patterns                    |
| -X    | --exclude-file      | File with exclude patterns          |
| -i    | --include           | Include patterns                    |
| -I    | --include-file      | File with include patterns          |
| -o    | --output            | Output file (default: context.txt)  |
| -d    | --dir               | Repository directory                |
| -v    | --verbose           | Show debug logs                     |
| -p    | --profile           | Use a saved profile                 |

## Key Concepts

### Basic File Selection

Two ways to select files:
1. **Exclude Mode** (`-x`): Start with all files, remove unwanted ones
   ```bash
   reposcope -x "build/" "*.log"  # Everything except builds and logs
   ```

2. **Include Mode** (`-i`): Start with no files, add wanted ones
   ```bash
   reposcope -i "src/*.py" "*.md"  # Only Python files and docs
   ```

### Pattern Matching

RepoScope uses .gitignore-style pattern matching:
- `*` matches any characters except /: `*.py`, `src/*.js`
- `?` matches one character: `test?.py` matches test1.py
- `**` matches directories: `src/**/*.py` matches all Python files under src
- `/` at start matches from root: `/test.py` only matches in root
- `/` at end matches directories: `build/` matches directory and contents
- `!` negates pattern: `!test_*.py` excludes test files

### Pattern Symmetry

Include and exclude modes are imcompatible (you have to pick one for one use!) but complementary:
```bash
# These do opposite things:
reposcope -i "*.py"           # Only Python files
reposcope -x "!*.py"          # Everything except Python files

# These are equivalent:
reposcope -x "*" "!*.py"      # Exclude all but Python
reposcope -i "*.py"           # Include only Python
```

### Profiles

Profiles help you save and reuse pattern collections. Instead of typing the same patterns repeatedly, you can save them in a profile and reuse them with a single command.

#### Profile Commands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `create` | `name --mode [include\|exclude]` | Create new profile |
| `delete` | `name` | Delete existing profile |
| `add` | `name pattern [pattern...]` | Add patterns to profile |
| `remove` | `name pattern [pattern...]` | Remove patterns from profile |
| `import` | `name file` | Import patterns from file |
| `export` | `name` | Export patterns to stdout |
| `list_profiles` | - | List all available profiles |
| `show` | `name` | Show profile details |

#### Basic Profile Usage

Create and use a profile:
```bash
# Create profile for Python development
reposcope profile create python --mode include
reposcope profile add python "*.py" "requirements.txt"

# Use the profile
reposcope -p python
```

List and inspect profiles:
```bash
# See all profiles
reposcope profile list_profiles

# Show specific profile
reposcope profile show python
```

#### Organizing Patterns with Profiles

You can create different profiles for different tasks:

```bash
# Profile for code review
reposcope profile create review --mode include
reposcope profile add review "src/" "tests/" "*.md"

# Profile for documentation work
reposcope profile create docs --mode include
reposcope profile add docs "**/*.md" "docs/" "examples/"

# Profile for excluding build artifacts
reposcope profile create clean --mode exclude
reposcope profile add clean "build/" "dist/" "*.pyc" "__pycache__/"
```

#### Using Pattern Files

You can import patterns from files:
```bash
# patterns.txt:
# Source files
*.py
src/
tests/
# Documentation
*.md
docs/

# Import patterns
reposcope profile create dev --mode include
reposcope profile import dev patterns.txt
```

#### Export and Share Profiles

Share your profiles with team members:
```bash
# Export patterns to a file
reposcope profile export myprofile > myprofile_patterns.txt

# Send file to colleague, they can import it:
reposcope profile create myprofile --mode include
reposcope profile import myprofile myprofile_patterns.txt
```

#### Pro Tips for Profiles

1. Combine include and exclude profiles:
   ```bash
   # Profile for source code
   reposcope profile create source --mode include
   reposcope profile add source "src/**/*.py"

   # Profile for artifacts to ignore
   reposcope profile create artifacts --mode exclude
   reposcope profile add artifacts "*.pyc" "__pycache__"

   # Use them together (include source, then exclude artifacts)
   reposcope -p source -x "*.pyc" "__pycache__"
   ```

2. Use project-specific profiles:
   ```bash
   # Django project profile
   reposcope profile create django --mode include
   reposcope profile add django "*.py" "templates/" "static/"
   
   # Flask project profile
   reposcope profile create flask --mode include
   reposcope profile add flask "*.py" "templates/" "static/" "instance/"
   ```

3. Create focused profiles:
   ```bash
   # Tests only
   reposcope profile create tests --mode include
   reposcope profile add tests "tests/**/*.py" "pytest.ini" "conftest.py"
   
   # Database related files
   reposcope profile create db --mode include
   reposcope profile add db "models.py" "migrations/" "schema.sql"
   ```

#### Profile Storage

Profiles are stored in `~/.config/reposcope/profiles.json`. Each profile maintains:
- Name
- Mode (include/exclude)
- List of patterns

#### Examples with Explanations

1. Development profile:
   ```bash
   reposcope profile create dev --mode include
   # Add source files
   reposcope profile add dev "src/**/*.py"
   # Add test files but exclude integration tests
   reposcope profile add dev "tests/" "!tests/integration/"
   # Add documentation
   reposcope profile add dev "*.md" "docs/"
   ```

2. Cleanup profile:
   ```bash
   reposcope profile create cleanup --mode exclude
   # Exclude common build artifacts
   reposcope profile add cleanup "build/" "dist/" "*.egg-info"
   # Exclude Python cache files
   reposcope profile add cleanup "**/__pycache__" "*.pyc" "*.pyo"
   # Exclude common editor/IDE files
   reposcope profile add cleanup ".vscode/" ".idea/" "*.swp"
   ```

3. Documentation profile:
   ```bash
   reposcope profile create docs --mode include
   # Include all documentation files
   reposcope profile add docs "**/*.md" "**/*.rst"
   # Include examples and tutorials
   reposcope profile add docs "docs/" "examples/" "tutorials/"
   # Exclude work in progress
   reposcope profile add docs "!**/draft/" "!**/*_wip.*"
   ```

## More Examples

### AI Code Review
```bash
# Share source and tests, exclude temporary files
reposcope -i "src/**/*.py" "tests/**/*.py" "!**/tmp/*"

# Everything except build artifacts and caches
reposcope -g -x "*.pyc" "**/__pycache__/"
```

### Documentation Work
```bash
# Only documentation files
reposcope -i "**/*.md" "docs/" "examples/"

# Share docs but exclude drafts
reposcope -i "docs/" "!docs/drafts/"
```

### Pro Tips
1. Combine .gitignore with extra exclusions:
   ```bash
   reposcope -g -x "*.tmp" "scratch/"
   ```

2. Override .gitignore exclusions:
   ```bash
   reposcope -g -x "!build/important.txt"
   ```

3. Use directory patterns effectively:
   ```bash
   # All files in src except tests
   reposcope -i "src/" "!src/tests/"
   ```

4. Chain patterns for complex selections:
   ```bash
   # Python files except tests, plus documentation
   reposcope -i "*.py" "!test_*.py" "docs/*.md"
   ```

## Development

1. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Run tests:
   ```bash
   pytest
   ```

## Limitations
- Currently Linux-only
- Requires Python 3.9+
- Large repositories might generate very big context files

## License

MIT License

## Contributing

Contributions are welcome! Open issues or pull requests on the project repository.