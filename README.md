# RepoScope

## What is RepoScope?

RepoScope is a command-line tool designed to simplify the process of sharing repository contents, especially when working with AI assistants or code review platforms. It solves a common problem developers face: how to quickly and easily share the entire context of a code project without manually copying and pasting individual files.

### The Problem

When collaborating on code or seeking assistance with a programming project, developers often need to share:
- Entire project structure
- Relevant source code files
- Configuration files
- Documentation

Traditionally, this meant:
- Manually selecting files
- Copying contents
- Risking omitting important files
- Spending time on repetitive tasks

### How RepoScope Helps

RepoScope automates the process of collecting and organizing repository contents by:
- Scanning your project directory
- Applying intelligent file selection
- Generating a comprehensive context file
- Supporting flexible inclusion/exclusion of files
- Allowing repeatable pattern-based selections

## Key Concepts

### File Selection Modes

RepoScope offers two primary modes of file selection:

1. **Exclude Mode**: 
   - Start with all files in the repository
   - Remove files matching specified patterns
   - Similar to how `.gitignore` works
   - Useful when you want to share most of your project, excluding only specific files

2. **Include Mode**:
   - Start with no files
   - Explicitly select files matching specified patterns
   - Useful when you want to share only specific parts of your project

### Pattern Matching

RepoScope uses `.gitignore`-style pattern matching:
- `*.py`: Matches all Python files in the current directory
- `src/*.js`: Matches JavaScript files directly in the `src/` directory
- `**/*.md`: Matches Markdown files in any subdirectory
- `docs/`: Excludes or includes entire directory

## Installation

```bash
pip install reposcope
```

### Requirements
- Python 3.9+
- Linux operating system (Windows/macOS support planned)

## Basic Usage

### Using .gitignore from the Current Directory
```bash
reposcope -g
```
This command reads the `.gitignore` file in the current directory and uses its patterns to exclude files from the generated context.

### Explicitly Including Files
```bash
reposcope -i "src/*.py" "src/*.js"
```
Collects only Python and JavaScript files from the `src/` directory.

## Output

Creates a `context.txt` file containing:
- Repository name
- File tree structure
- Full contents of selected files

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

This output is ideal for:
- Sharing code with AI assistants
- Code reviews
- Documentation generation
- Simplified project snapshots

## Modes of Operation

### 1. Exclude Mode
Exclude specific files or directories:
```bash
# Use current directory's .gitignore
reposcope -g

# Manually specify exclude patterns
reposcope -x "*.log" "temp/*"

# Use an exclude patterns file
reposcope -X exclude.txt
```

### 2. Include Mode
Select specific files to include:
```bash
# Specify include patterns
reposcope -i "*.py" "src/*.js"

# Use an include patterns file
reposcope -I include.txt
```

**Note:** Do not mix exclude and include patterns in a single command.
```bash
# This is INVALID
reposcope -g -x "*.log" -i "*.py"
```

## Profiles

Profiles allow you to save and reuse file selection patterns, making repeated context generation consistent and efficient.

### Create a Profile
```bash
# Create an include profile
reposcope profile create my_profile --mode include

# Add patterns to the profile
reposcope profile add my_profile "*.py" "docs/*.md"

# Use the profile
reposcope -p my_profile
```

### Profile Commands
- `create`: Create a new profile
- `add`: Add patterns to a profile
- `remove`: Remove patterns from a profile
- `import`: Import patterns from a file
- `export`: Export profile patterns
- `list_profiles`: List all profiles
- `show`: Display profile details
- `delete`: Remove a profile

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

## Common Use Cases

1. **AI Code Review**
   ```bash
   # Share only source code for review
   reposcope -i "src/*.py" "tests/*.py"
   ```

2. **Project Documentation**
   ```bash
   # Generate context for documentation
   reposcope -i "README.md" "docs/*" "*.rst"
   ```

3. **Selective Sharing**
   ```bash
   # Exclude build and temp files
   reposcope -x "build/*" "*.log" "temp/"
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