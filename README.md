# RepoScope 🔍

Grabs your repo files and dumps them into one document - super handy when you need to share code with AI assistants. Made it because I was tired of copy-pasting files one by one into ChatGPT chats.

## Install
```bash
pip install reposcope
```
Python 3.9+ required. Linux only for now (Windows/macOS later maybe).

## Quick Start

Default mode - just use your .gitignore:
```bash
# In your project directory:
reposcope -g
```

Or pick specific files:
```bash
# Just Python and JS files from src:
reposcope -i "src/*.py" "src/*.js"
```

You'll get a `context.txt` that looks like this:
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

--- src/utils.py ---
def add(a, b):
    return a + b

--- README.md ---
# My Project
A simple example...
```

## Two Ways to Use It

### 1. Exclude Mode - Skip Stuff You Don't Want

```bash
# Use .gitignore (easiest)
reposcope -g

# Skip specific files
reposcope -x "*.log" "temp/*"     # -x or --exclude or --ignore
reposcope -X exclude.txt          # -X or --exclude-file or --ignore-file

# Mix them
reposcope -g -x "*.log" -X more_excludes.txt
```

### 2. Include Mode - Pick Exactly What You Want

```bash
# Pick specific files
reposcope -i "*.py" "src/*.js"    # -i or --include
reposcope -I include.txt          # -I or --include-file
```

Files are matched using .gitignore-style patterns:
```
*.py            # All Python files
src/*.js        # JS files in src/
docs/**/*.md    # Markdown files in docs/ and subdirs
node_modules/   # Entire directory
config.json     # Specific file
```

## All Options

| Short | Long                             | What it Does                          |
|-------|----------------------------------|---------------------------------------|
| -g    | --use-gitignore                 | Use .gitignore                        |
| -x    | --exclude, --ignore             | Patterns to exclude                   |
| -X    | --exclude-file, --ignore-file   | File with exclude patterns           |
| -i    | --include                       | Patterns to include                   |
| -I    | --include-file                  | File with include patterns           |
| -o    | --output                        | Output file (default: context.txt)    |
| -d    | --dir                           | Different directory                   |
| -v    | --verbose                       | Show what's happening                 |

## Tips

1. Start with `-g` if you have a good .gitignore

2. Too much stuff? Exclude some:
   ```bash
   reposcope -g -x "*.cache" ".env"
   ```

3. Need specific files? Use include:
   ```bash
   reposcope -i "src/*.py" "*.md"
   ```

4. Doing it often? Save patterns in a file:
   ```bash
   # frontend.txt
   src/components/*.jsx
   src/styles/*.css
   ```
   ```bash
   reposcope -I frontend.txt
   ```

## License

MIT. Do whatever.

## Contributing

It's a small tool but if you spot bugs or have ideas - feel free to open an issue.