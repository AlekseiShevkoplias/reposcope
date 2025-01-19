#!/usr/bin/env python3
import os
import logging
from pathlib import Path
from typing import List, Set
import fnmatch

logger = logging.getLogger(__name__)

class RepoScope:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.patterns: Set[str] = set()
        self.is_include_mode = False
        logger.info(f"Initialized RepoScope with root directory: {self.root_dir}")

    def _process_gitignore_pattern(self, pattern: str) -> List[str]:
        """Process a single pattern according to .gitignore rules."""
        if not pattern or pattern.startswith('#'):
            return []

        patterns = []
        
        # Handle directory patterns
        if pattern.endswith('/'):
            pattern = pattern[:-1]
            # Add both with and without trailing slash
            patterns.extend([pattern, f"{pattern}/"])
        else:
            patterns.append(pattern)

        # If pattern doesn't start with /, add **/ variant to match in subdirectories
        if not pattern.startswith('/'):
            for p in patterns.copy():
                patterns.append(f"**/{p}")

        # If pattern starts with /, remove it as we're using relative paths
        patterns = [p[1:] if p.startswith('/') else p for p in patterns]

        return patterns

    def use_gitignore(self) -> 'RepoScope':
        """Load patterns from .gitignore file."""
        gitignore_path = self.root_dir / '.gitignore'
        if gitignore_path.exists():
            logger.info(f"Loading patterns from .gitignore: {gitignore_path}")
            self._load_patterns_from_file(gitignore_path)
        else:
            logger.warning(f"No .gitignore found in {self.root_dir}")
        return self

    def use_ignore_file(self, ignore_file: str) -> 'RepoScope':
        """Load patterns from specified ignore file using .gitignore rules."""
        ignore_path = Path(ignore_file)
        if ignore_path.exists():
            logger.info(f"Loading patterns from ignore file: {ignore_path}")
            self._load_patterns_from_file(ignore_path)
        else:
            logger.warning(f"Ignore file not found: {ignore_path}")
        return self

    def use_ignore_patterns(self, patterns: List[str]) -> 'RepoScope':
        """Add ignore patterns directly, processing them according to .gitignore rules."""
        if patterns:
            logger.info(f"Adding ignore patterns: {patterns}")
            for pattern in patterns:
                processed_patterns = self._process_gitignore_pattern(pattern)
                self.patterns.update(processed_patterns)
                logger.debug(f"Pattern '{pattern}' expanded to: {processed_patterns}")
        return self

    def use_include_file(self, include_file: str) -> 'RepoScope':
        """Switch to include mode and load patterns from include file using .gitignore rules."""
        self.is_include_mode = True
        self.patterns.clear()
        include_path = Path(include_file)
        if include_path.exists():
            logger.info(f"Loading include patterns from file: {include_path}")
            self._load_patterns_from_file(include_path)
        else:
            logger.warning(f"Include file not found: {include_path}")
        return self

    def use_include_patterns(self, patterns: List[str]) -> 'RepoScope':
        """Switch to include mode and use specified patterns, processing them according to .gitignore rules."""
        logger.info(f"Switching to include mode with patterns: {patterns}")
        self.is_include_mode = True
        self.patterns.clear()
        if patterns:
            for pattern in patterns:
                processed_patterns = self._process_gitignore_pattern(pattern)
                self.patterns.update(processed_patterns)
                logger.debug(f"Pattern '{pattern}' expanded to: {processed_patterns}")
        return self

    def _load_patterns_from_file(self, file_path: Path):
        """Load and process patterns from a file according to .gitignore rules."""
        patterns_before = len(self.patterns)
        with open(file_path, 'r') as f:
            for line in f:
                pattern = line.strip()
                processed_patterns = self._process_gitignore_pattern(pattern)
                if processed_patterns:
                    self.patterns.update(processed_patterns)
                    logger.debug(f"Pattern '{pattern}' expanded to: {processed_patterns}")
        
        patterns_added = len(self.patterns) - patterns_before
        logger.debug(f"Loaded {patterns_added} patterns from {file_path}")

    def _should_skip_directory(self, dir_path: Path) -> bool:
        """Check if directory should be skipped based on patterns."""
        if self.is_include_mode:
            return False

        rel_path = str(dir_path.relative_to(self.root_dir))
        if not rel_path:  # Root directory
            return False

        # Add trailing slash to match directory patterns
        rel_path_with_slash = f"{rel_path}/"
        
        for pattern in self.patterns:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path_with_slash, pattern):
                logger.debug(f"Skipping directory {rel_path} (matched pattern: {pattern})")
                return True
        return False

    def _should_include_file(self, file_path: Path) -> bool:
        """Determine if a file should be included based on current mode and patterns."""
        rel_path = str(file_path.relative_to(self.root_dir))
        
        # Always skip .git directory
        if ".git/" in f"{rel_path}/":
            return False

        if self.is_include_mode:
            # Include mode: file must match at least one pattern
            should_include = any(fnmatch.fnmatch(rel_path, pattern) for pattern in self.patterns)
            logger.debug(f"Include mode - File {rel_path}: {'✓' if should_include else '✗'}")
            return should_include
        else:
            # Ignore mode: file must not match any pattern
            for pattern in self.patterns:
                if fnmatch.fnmatch(rel_path, pattern):
                    logger.debug(f"Ignore mode - File {rel_path}: ✗ (matched pattern: {pattern})")
                    return False
            logger.debug(f"Ignore mode - File {rel_path}: ✓")
            return True

    def collect_files(self) -> List[Path]:
        """Collect all files based on current configuration."""
        logger.info(f"Starting file collection in {'include' if self.is_include_mode else 'ignore'} mode")
        logger.info(f"Current patterns: {self.patterns}")
        
        included_files = []
        
        for root, dirs, files in os.walk(self.root_dir, topdown=True):
            root_path = Path(root)

            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if not self._should_skip_directory(root_path / d)]

            for file in files:
                file_path = root_path / file
                if self._should_include_file(file_path):
                    included_files.append(file_path)

        logger.info(f"Collected {len(included_files)} files")
        return included_files

    def generate_context_file(self, output_file: str):
        """Generate the context file with directory tree and file contents."""
        logger.info(f"Generating context file: {output_file}")
        files = self.collect_files()
        
        with open(output_file, 'w') as f:
            # Write root directory name
            f.write(f"Repository: {self.root_dir.name}\n\n")
            
            # Write file tree
            f.write("File Tree:\n")
            for file in sorted(files):
                rel_path = file.relative_to(self.root_dir)
                f.write(f"└── {rel_path}\n")
            f.write("\n")
            
            # Write file contents
            f.write("File Contents:\n")
            written_files = 0
            for file in sorted(files):
                rel_path = file.relative_to(self.root_dir)
                f.write(f"\n--- {rel_path} ---\n")
                try:
                    with open(file, 'r') as content_file:
                        f.write(content_file.read())
                    written_files += 1
                except UnicodeDecodeError:
                    f.write("[Binary file]\n")
                    logger.warning(f"Skipped binary file: {rel_path}")
                except Exception as e:
                    f.write(f"[Error reading file: {str(e)}]\n")
                    logger.error(f"Error reading file {rel_path}: {str(e)}")
                f.write("\n")
        
        logger.info(f"Successfully wrote {written_files} files to {output_file}")