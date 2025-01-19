#!/usr/bin/env python3
import argparse
import logging
import sys
from reposcope.core import RepoScope

def setup_logging(verbose: bool):
    """Configure logging based on verbosity level."""
    # Remove any existing handlers to ensure clean setup
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
            
    level = logging.DEBUG if verbose else logging.WARNING
    
    # Configure handler for stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    
    # Setup root logger
    root.setLevel(level)
    root.addHandler(handler)
    
    # Ensure propagation for our module's logger
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    logger.propagate = True

def main():
    parser = argparse.ArgumentParser(
        description="RepoScope - Generate repository context files for LLMs"
    )
    parser.add_argument(
        "-d", "--dir", 
        default=".",
        help="Root directory of the repository (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output",
        default="context.txt",
        help="Output file path (default: context.txt)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    # Ignore-based selection options
    ignore_group = parser.add_argument_group('Ignore-based selection')
    ignore_group.add_argument(
        "-g", "--use-gitignore",
        action="store_true",
        help="Use patterns from .gitignore file"
    )
    ignore_group.add_argument(
        "-x", "--ignore", "--exclude",
        dest="ignore",
        nargs="*",
        help="Specify patterns to exclude"
    )
    ignore_group.add_argument(
        "-X", "--ignore-file", "--exclude-file",
        dest="ignore_file",
        help="Use patterns from specified exclude file"
    )

    # Include-based selection options
    include_group = parser.add_argument_group('Include-based selection')
    include_group.add_argument(
        "-i", "--include",
        nargs="*",
        help="Specify patterns to include"
    )
    include_group.add_argument(
        "-I", "--include-file",
        help="Use patterns from specified include file"
    )

    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Log startup info in verbose mode
    logger.debug("RepoScope starting up")
    logger.debug(f"Arguments: {args}")

    # Check for mixing of modes
    has_include = bool(args.include_file or args.include)
    has_ignore = bool(args.use_gitignore or args.ignore_file or args.ignore)
    
    if has_include and has_ignore:
        logger.warning("Both ignore and include options specified. Include patterns will take precedence.")

    # Create RepoScope instance
    try:
        logger.debug(f"Initializing RepoScope with directory: {args.dir}")
        scope = RepoScope(args.dir)

        # Check if we're in include mode
        if has_include:
            if args.include_file:
                logger.debug(f"Using include file: {args.include_file}")
                scope.use_include_file(args.include_file)
            if args.include:
                logger.debug(f"Using include patterns: {args.include}")
                scope.use_include_patterns(args.include)
        else:
            # Ignore mode - apply specified ignore patterns
            if args.use_gitignore:
                logger.debug("Using .gitignore patterns")
                scope.use_gitignore()
            if args.ignore_file:
                logger.debug(f"Using ignore file: {args.ignore_file}")
                scope.use_ignore_file(args.ignore_file)
            if args.ignore:
                logger.debug(f"Using ignore patterns: {args.ignore}")
                scope.use_ignore_patterns(args.ignore)

        logger.debug(f"Generating context file: {args.output}")
        scope.generate_context_file(args.output)
        print(f"Generated context file: {args.output}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()