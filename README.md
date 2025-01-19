# RepoScope 🔍

A tiny tool that makes sharing code with AI much easier. It dumps files from a directory into a single well-organized document - so you can show your whole project to ChatGPT or Claude.

I made this because I was tired of copy-pasting files one by one into AI chats. Maybe you'll find it useful too.

## Requirements

- Linux (Windows and macOS not supported yet)
- Python 3.8 or higher

## Why RepoScope?

Working with AI is great until you need to show it your whole codebase. Copying files manually is a pain, and it's easy to miss important stuff or accidentally share sensitive or unneccesary files. This tool just:
- Makes a nice file tree so AI understands your project structure
- Copies all the relevant file contents
- Respects your `.gitignore`
- Lets you pick exactly what to include or exclude

## Quick Start

Install it:
```bash
pip install reposcope
```

Run it in your project:
```bash
# Most common use case - respect .gitignore
reposcope --use-gitignore

# Or pick specific files
reposcope --include "*.py" "src/*.js"
```

That's it - you'll get a `context.txt` ready to paste into your AI chat.

## How to Use

There are two ways to use it:

### 1. Ignore Mode (Skip Files)

When you want everything EXCEPT certain files:
```bash
# Use your .gitignore (probably what you want)
reposcope --use-gitignore

# Use a custom ignore file
reposcope --ignore-file my_ignores.txt

# Ignore stuff directly
reposcope --ignore "*.log" "temp/*"

# Mix and match
reposcope --use-gitignore --ignore "*.log" --ignore-file custom_ignore.txt
```

### 2. Include Mode (Pick Files)

When you only want specific files:
```bash
# Pick files by pattern
reposcope --include "*.py" "src/*.js"

# Or keep patterns in a file
reposcope --include-file include.txt
```

### Pattern Format

Works just like .gitignore:
```
*.py            # grab all Python files
src/*.js        # JS files in src directory
docs/**/*.md    # markdown files in docs and subdirs
node_modules/   # entire directory
config.json     # specific file
```

### Other Stuff You Can Do

```bash
# Change output file name
reposcope --output something.txt

# Run in a different directory
reposcope --dir ../other-project

# See what's happening
reposcope --use-gitignore --verbose
```

## What You Get

A clean text file that looks like this:
```
Repository: my-project

File Tree:
└── src/main.py
└── docs/README.md
└── config.json

File Contents:

--- src/main.py ---
[file content here]

--- docs/README.md ---
[file content here]

--- config.json ---
[file content here]
```

## Pro Tips

1. Start with `--use-gitignore` - it usually does what you want
2. If you're getting too much stuff, just pick what you need:
   ```bash
   reposcope --include "src/*.py" "*.md"
   ```
3. Create separate include files for different tasks:
   ```bash
   # frontend.txt
   src/components/*.jsx
   src/styles/*.css
   ```
   Then:
   ```bash
   reposcope --include-file frontend.txt --output frontent_context.txt
   ```

## License

MIT - do whatever you want with it.

## Contributing

It's a tiny tool but if you spot bugs or have ideas, open an issue or PR!