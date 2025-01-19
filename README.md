# RepoScope 🔍

A tiny tool that dumps your repo files into a single document for easy sharing with AI assistants. Made because I was tired of copy-pasting files one by one into ChatGPT chats.

## Requirements
- Linux only (Windows and macOS not supported yet)
- Python >= 3.9

## Install
```bash
pip install reposcope
```

## Usage

Run in your project directory:
```bash
# Respect .gitignore (what you want most of the time)
reposcope --use-gitignore

# Or pick specific files
reposcope --include "*.py" "src/*.js"
```

You'll get `context.txt` with your files.

## How it Works

Two modes to use:

### 1. Ignore Mode

Skip some files:
```bash
# Use .gitignore
reposcope --use-gitignore

# Use custom ignore file
reposcope --ignore-file my_ignores.txt

# Ignore directly
reposcope --ignore "*.log" "temp/*"

# Mix them
reposcope --use-gitignore --ignore "*.log" --ignore-file custom_ignore.txt
```

### 2. Include Mode

Pick specific files:
```bash
# By pattern
reposcope --include "*.py" "src/*.js"

# From file
reposcope --include-file include.txt
```

### Patterns

Work like in .gitignore:
```
*.py            # Python files
src/*.js        # JS in src directory
docs/**/*.md    # markdown in docs and subdirs
node_modules/   # entire directory
config.json     # specific file
```

### Extra Options

```bash
# Change output name
reposcope --output something.txt

# Different directory
reposcope --dir ../other-project

# See what's happening
reposcope --use-gitignore --verbose
```

## Output Example

You get a text file like this:
```
Repository: my-project

File Tree:
└── src/main.py
└── docs/README.md
└── config.json

File Contents:

--- src/main.py ---
[content here]

--- docs/README.md ---
[content here]

--- config.json ---
[content here]
```

## Tips

1. Start with `--use-gitignore` - probably what you want
2. If getting too much stuff, pick what you need:
   ```bash
   reposcope --include "src/*.py" "*.md"
   ```
3. Keep patterns in files for different tasks:
   ```bash
   # frontend.txt
   src/components/*.jsx
   src/styles/*.css
   ```
   Then:
   ```bash
   reposcope --include-file frontend.txt
   ```

## License

MIT - do whatever

## Contributing

Small tool but if you spot bugs or have ideas, open an issue.