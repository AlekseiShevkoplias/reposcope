import os
import logging
from pathlib import Path
from typing import List, Tuple
import fnmatch

logger = logging.getLogger(__name__)

class RepoScope:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()
        self.patterns: List[Tuple[str, bool]] = []  # [(pattern, is_negated)]
        self.is_include_mode = False
        logger.info(f"Initialized RepoScope with root directory: {self.root_dir}")

    def _process_gitignore_pattern(self, pattern: str) -> List[Tuple[str, bool]]:
        """
        Process a single pattern according to .gitignore rules.
        Returns a list of tuples (pattern, is_negated) for each processed variant.
        """
        if not pattern or pattern.startswith('#'):
            return []

        # Handle negation
        is_negated = pattern.startswith('!')
        if is_negated:
            pattern = pattern[1:].strip()  # Remove ! and any extra whitespace
            if not pattern:  # If pattern is just "!" or "! " etc.
                return []

        patterns = []
        
        # Handle directory patterns
        if pattern.endswith('/'):
            pattern = pattern[:-1]
            patterns.extend([
                pattern,            # Match the directory itself
                f"{pattern}/*",     # Match direct children
                f"{pattern}/**/*"   # Match all descendants
            ])
        else:
            patterns.append(pattern)

        # If pattern doesn't start with /, add **/ variant
        if not pattern.startswith('/'):
            base_patterns = patterns.copy()
            for p in base_patterns:
                if not any(p.startswith(prefix) for prefix in ["**/", "**"]):
                    patterns.append(f"**/{p}")

        # If pattern starts with /, remove it as we're using relative paths
        return [(p[1:] if p.startswith('/') else p, is_negated) for p in patterns]

    def use_gitignore(self) -> 'RepoScope':
        """Load patterns from .gitignore file."""
        gitignore_path = self.root_dir / '.gitignore'
        if gitignore_path.exists():
            logger.info(f"Loading patterns from .gitignore: {gitignore_path}")
            self._load_patterns_from_file(gitignore_path)
        else:
            logger.warning(f"No .gitignore found in {self.root_dir}")
        return self

    def use_ignore_patterns(self, patterns: List[str]) -> 'RepoScope':
        """Add ignore patterns directly."""
        if patterns:
            logger.info(f"Adding ignore patterns: {patterns}")
            for pattern in patterns:
                processed_patterns = self._process_gitignore_pattern(pattern)
                for p, n in processed_patterns:
                    self.patterns.append((p, n))
                    logger.debug(f"Pattern '{pattern}' {'(negated) ' if n else ''}expanded to: {p}")
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

    def use_include_patterns(self, patterns: List[str]) -> 'RepoScope':
        """Switch to include mode and use specified patterns."""
        logger.info(f"Switching to include mode with patterns: {patterns}")
        self.is_include_mode = True
        self.patterns = []  # Clear existing patterns
        if patterns:
            for pattern in patterns:
                processed_patterns = self._process_gitignore_pattern(pattern)
                for p, n in processed_patterns:
                    self.patterns.append((p, n))
                    logger.debug(f"Pattern '{pattern}' {'(negated) ' if n else ''}expanded to: {p}")
        return self

    def use_include_file(self, include_file: str) -> 'RepoScope':
        """Switch to include mode and load patterns from include file."""
        self.is_include_mode = True
        self.patterns = []  # Clear existing patterns
        include_path = Path(include_file)
        if include_path.exists():
            logger.info(f"Loading include patterns from file: {include_path}")
            self._load_patterns_from_file(include_path)
        else:
            logger.warning(f"Include file not found: {include_path}")
        return self

    def _load_patterns_from_file(self, file_path: Path):
        """Load and process patterns from a file according to .gitignore rules."""
        patterns_before = len(self.patterns)
        with open(file_path, 'r') as f:
            for line in f:
                pattern = line.strip()
                processed_patterns = self._process_gitignore_pattern(pattern)
                for p, n in processed_patterns:
                    self.patterns.append((p, n))
                    if processed_patterns:  # Only log if pattern was valid
                        logger.debug(f"Pattern '{pattern}' {'(negated) ' if n else ''}expanded to: {p}")
        
        patterns_added = len(self.patterns) - patterns_before
        logger.debug(f"Loaded {patterns_added} patterns from {file_path}")

    def _should_skip_directory(self, dir_path: Path) -> bool:
        """Check if directory should be skipped based on patterns."""
        if self.is_include_mode:
            return False

        rel_path = str(dir_path.relative_to(self.root_dir))
        if not rel_path:  # Root directory
            return False

        # Add trailing slash for directory matching
        rel_path_with_slash = f"{rel_path}/"
        
        # In exclude mode, directories are skipped if they match any non-negated pattern
        # and don't match any subsequent negated pattern
        is_skipped = False
        for pattern, is_negated in self.patterns:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path_with_slash, pattern):
                is_skipped = not is_negated  # Flip skip status based on negation
        
        if is_skipped:
            logger.debug(f"Skipping directory {rel_path}")
        return is_skipped

    def _should_include_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be included based on current mode and patterns.
        
        In exclude mode:
            - Files are included by default
            - Files matching non-negated patterns are excluded
            - Files matching negated patterns are re-included
        
        In include mode:
            - Files are excluded by default
            - Files matching non-negated patterns are included
            - Files matching negated patterns are re-excluded
        """
        rel_path = str(file_path.relative_to(self.root_dir))
        
        # Always skip .git directory
        if ".git/" in f"{rel_path}/":
            return False

        if self.is_include_mode:
            # Start with excluded in include mode
            is_included = False
            for pattern, is_negated in self.patterns:
                if fnmatch.fnmatch(rel_path, pattern):
                    is_included = not is_negated
            
            if is_included:
                logger.debug(f"Including file {rel_path} (matched include pattern)")
            return is_included
        else:
            # Start with included in exclude mode
            is_included = True
            for pattern, is_negated in self.patterns:
                if fnmatch.fnmatch(rel_path, pattern):
                    is_included = is_negated
            
            if not is_included:
                logger.debug(f"Excluding file {rel_path} (matched exclude pattern)")
            return is_included

    def collect_files(self) -> List[Path]:
        """Collect all files based on current configuration."""
        logger.info(f"Starting file collection in {'include' if self.is_include_mode else 'exclude'} mode")
        if self.patterns:
            logger.info("Current patterns:")
            for pattern, is_negated in self.patterns:
                logger.info(f"  {'!' if is_negated else ' '}{pattern}")
        
        included_files = []
        
        for root, dirs, files in os.walk(self.root_dir, topdown=True):
            root_path = Path(root)

            # Modify dirs in-place to skip directories based on patterns
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