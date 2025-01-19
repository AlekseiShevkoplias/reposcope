#!/usr/bin/env python3
import argparse
import logging
import sys
from pathlib import Path
from reposcope.core import RepoScope
from reposcope.profiles import ProfileManager, ProfileError

def setup_logging(verbose: bool):
    """Configure logging to include log levels and output to stderr."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',  # Include log level names
        stream=sys.stderr,  # Explicitly output to stderr
        force=True  # Force reconfiguration to ensure stderr output
    )
    logging.debug("Verbose logging enabled")  # Add a debug log to ensure it's captured


def setup_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate repository context files for LLMs"
    )
    subparsers = parser.add_subparsers(dest='command')

    # Scan command (main functionality)
    scan = subparsers.add_parser('scan', help='Generate context file (default command)')
    _setup_scan_arguments(scan)
    scan.set_defaults(command='scan')  # Make 'scan' the default

    # Profile command group
    profile = subparsers.add_parser('profile', help='Manage profiles')
    profile_sub = profile.add_subparsers(dest='action', required=True)
    _setup_profile_arguments(profile_sub)

    return parser


def _setup_scan_arguments(parser):
    """Setup arguments for the main scan command."""
    parser.add_argument(
        "-d", "--dir", 
        default=".",
        help="Root directory of the repository"
    )
    parser.add_argument(
        "-o", "--output",
        default="context.txt",
        help="Output file path"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show what's happening"
    )
    
    # Profile usage
    parser.add_argument(
        "-p", "--profile",
        help="Use saved profile"
    )

    # Basic operation modes
    parser.add_argument(
        "-g", "--use-gitignore",
        action="store_true",
        help="Use patterns from .gitignore file"
    )

    # Ignore-based selection
    parser.add_argument(
        "-x", "--exclude", "--ignore",
        dest="ignore",
        nargs="*",
        help="Specify patterns to exclude"
    )
    parser.add_argument(
        "-X", "--exclude-file", "--ignore-file",
        dest="ignore_file",
        help="Use patterns from specified exclude file"
    )

    # Include-based selection
    parser.add_argument(
        "-i", "--include",
        nargs="*",
        help="Specify patterns to include"
    )
    parser.add_argument(
        "-I", "--include-file",
        help="Use patterns from specified include file"
    )

def _setup_profile_arguments(subparsers):
    """Setup arguments for profile management commands."""
    # Create profile
    create = subparsers.add_parser('create', help='Create new profile')
    create.add_argument('name', help='Profile name')
    create.add_argument('--mode', choices=['include', 'exclude'], required=True,
                       help='Profile mode')

    # Delete profile
    delete = subparsers.add_parser('delete', help='Delete profile')
    delete.add_argument('name', help='Profile name')

    # List profiles
    subparsers.add_parser('list_profiles', help='List available profiles')

    # Show profile
    show = subparsers.add_parser('show', help='Show profile details')
    show.add_argument('name', help='Profile name')

    # Add patterns
    add = subparsers.add_parser('add', help='Add patterns to profile')
    add.add_argument('name', help='Profile name')
    add.add_argument('patterns', nargs='+', help='Patterns to add')

    # Remove patterns
    remove = subparsers.add_parser('remove', help='Remove patterns from profile')
    remove.add_argument('name', help='Profile name')
    remove.add_argument('patterns', nargs='+', help='Patterns to remove')

    # Import patterns
    import_cmd = subparsers.add_parser('import', help='Import patterns from file')
    import_cmd.add_argument('name', help='Profile name')
    import_cmd.add_argument('file', help='File to import patterns from')

    # Export patterns
    export = subparsers.add_parser('export', help='Export patterns to stdout')
    export.add_argument('name', help='Profile name')

def handle_profile(args, profile_mgr):
    """Handle profile management commands."""
    try:
        if args.action == 'create':
            profile = profile_mgr.create(args.name, args.mode)
            print(f"Created profile: {profile.summary()}")

        elif args.action == 'delete':
            profile_mgr.delete(args.name)
            print(f"Deleted profile: {args.name}")

        elif args.action == 'list_profiles':
            profiles = profile_mgr.get_profiles()
            if not profiles:
                print("No profiles found")
                return
            print("Available profiles:")
            for profile in profiles:
                print(f"  {profile.summary()}")

        elif args.action == 'show':
            profile = profile_mgr.get(args.name)
            print(profile.details())

        elif args.action == 'add':
            added = profile_mgr.add_patterns(args.name, args.patterns)
            if added:
                print(f"Added to {args.name}:")
                for pattern in added:
                    print(f"  {pattern}")
            else:
                print("No new patterns added (already exist)")

        elif args.action == 'remove':
            removed = profile_mgr.remove_patterns(args.name, args.patterns)
            if removed:
                print(f"Removed from {args.name}:")
                for pattern in removed:
                    print(f"  {pattern}")
            else:
                print("No patterns removed (not found)")

        elif args.action == 'import':
            added = profile_mgr.import_patterns(args.name, args.file)
            if added:
                print(f"Imported to {args.name}:")
                for pattern in added:
                    print(f"  {pattern}")
            else:
                print("No new patterns imported (already exist)")

        elif args.action == 'export':
            print(profile_mgr.export_patterns(args.name))

    except ProfileError as e:
        logging.error(str(e))
        sys.exit(1)

def handle_scan(args, profile_mgr):
    """Handle the main scan command."""
    logger = logging.getLogger(__name__)
    logger.debug("Starting file collection with verbose logging enabled.")

    try:
        scope = RepoScope(args.dir)

        if args.profile:
            profile = profile_mgr.get(args.profile)
            if profile.mode == 'include':
                scope.use_include_patterns(profile.patterns)
            else:
                scope.use_gitignore()
                scope.use_ignore_patterns(profile.patterns)

        if args.include or args.include_file:
            if args.include_file:
                scope.use_include_file(args.include_file)
            if args.include:
                scope.use_include_patterns(args.include)
        else:
            if args.use_gitignore:
                scope.use_gitignore()
            if args.ignore_file:
                scope.use_ignore_file(args.ignore_file)
            if args.ignore:
                scope.use_ignore_patterns(args.ignore)

        scope.generate_context_file(args.output)
        print(f"Generated context file: {args.output}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

def main(): 
    """ Entrypoint for the reposcope CLI. If the user has not specified a subcommand 
    ('scan' or 'profile'), this function forces 'scan' to become the default subcommand, 
    allowing top-level flags like -g or --exclude to work as intended. """
    parser = setup_parser()
    
    # If no arguments provided, or first argument is not a known command
    if len(sys.argv) == 1:
        sys.argv.append('scan')
    else:
        first_arg = sys.argv[1]
        if first_arg not in ['scan', 'profile', '-h', '--help']:
            sys.argv.insert(1, 'scan')

    args = parser.parse_args()
    
    # Always setup logging. For scan command, use verbose flag 
    # For profile commands, default to warning level
    verbose = hasattr(args, 'verbose') and args.verbose
    setup_logging(verbose)
    
    profile_mgr = ProfileManager()

    if args.command == 'scan':
        handle_scan(args, profile_mgr)
    elif args.command == 'profile':
        handle_profile(args, profile_mgr)

if __name__ == "__main__":
    main()