#!/usr/bin/env python3
import pytest
import sys
import os
import tempfile
import argparse
from pathlib import Path
from unittest.mock import patch, Mock, call

from reposcope.cli import (
    setup_parser, 
    main, 
    handle_scan, 
    handle_profile,
    setup_logging
)
from reposcope.profiles import ProfileManager, ProfileError

class TestCLIParser:
    @pytest.fixture
    def parser(self):
        """Create a parser for testing."""
        return setup_parser()

    def test_default_scan_arguments(self, parser):
        """Test default arguments for scan command."""
        # Parse minimal scan command
        args = parser.parse_args(['scan'])
        
        assert args.command == 'scan'
        assert args.dir == '.'
        assert args.output == 'context.txt'
        assert not args.verbose
        assert not args.use_gitignore
        assert args.ignore is None
        assert args.ignore_file is None
        assert args.include is None
        assert args.include_file is None

    def test_scan_with_all_options(self, parser):
        """Test scan command with all possible options."""
        args = parser.parse_args([
            'scan', 
            '-d', '/path/to/repo', 
            '-o', 'custom_context.txt', 
            '-v', 
            '-g', 
            '-x', '*.log', 'build/', 
            '-X', 'exclude.txt', 
            '-i', '*.py', 'src/', 
            '-I', 'include.txt',
            '-p', 'my_profile'
        ])

        assert args.command == 'scan'
        assert args.dir == '/path/to/repo'
        assert args.output == 'custom_context.txt'
        assert args.verbose
        assert args.use_gitignore
        assert args.ignore == ['*.log', 'build/']
        assert args.ignore_file == 'exclude.txt'
        assert args.include == ['*.py', 'src/']
        assert args.include_file == 'include.txt'
        assert args.profile == 'my_profile'

    def test_profile_create_command(self, parser):
        """Test profile create command with required arguments."""
        args = parser.parse_args(['profile', 'create', 'test_profile', '--mode', 'include'])
        
        assert args.command == 'profile'
        assert args.action == 'create'
        assert args.name == 'test_profile'
        assert args.mode == 'include'

    def test_profile_create_mode_choices(self, parser):
        """Test profile create command mode choices."""
        # Valid modes should pass
        parser.parse_args(['profile', 'create', 'test_profile', '--mode', 'include'])
        parser.parse_args(['profile', 'create', 'test_profile', '--mode', 'exclude'])

        # Invalid mode should raise an error
        with pytest.raises(SystemExit):
            parser.parse_args(['profile', 'create', 'test_profile', '--mode', 'invalid'])

    def test_profile_subcommands(self, parser):
        """Test various profile subcommands."""
        # Delete profile
        args = parser.parse_args(['profile', 'delete', 'test_profile'])
        assert args.command == 'profile'
        assert args.action == 'delete'
        assert args.name == 'test_profile'

        # List profiles
        args = parser.parse_args(['profile', 'list_profiles'])
        assert args.command == 'profile'
        assert args.action == 'list_profiles'

        # Show profile
        args = parser.parse_args(['profile', 'show', 'test_profile'])
        assert args.command == 'profile'
        assert args.action == 'show'
        assert args.name == 'test_profile'

        # Add patterns
        args = parser.parse_args(['profile', 'add', 'test_profile', '*.py', 'src/'])
        assert args.command == 'profile'
        assert args.action == 'add'
        assert args.name == 'test_profile'
        assert args.patterns == ['*.py', 'src/']

        # Remove patterns
        args = parser.parse_args(['profile', 'remove', 'test_profile', '*.log', 'build/'])
        assert args.command == 'profile'
        assert args.action == 'remove'
        assert args.name == 'test_profile'
        assert args.patterns == ['*.log', 'build/']

        # Import patterns
        args = parser.parse_args(['profile', 'import', 'test_profile', 'patterns.txt'])
        assert args.command == 'profile'
        assert args.action == 'import'
        assert args.name == 'test_profile'
        assert args.file == 'patterns.txt'
        # assert args.gitignore

        # Export patterns
        args = parser.parse_args(['profile', 'export', 'test_profile'])
        assert args.command == 'profile'
        assert args.action == 'export'
        assert args.name == 'test_profile'
        # assert args.gitignore


class TestCLIFunctionality:
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)

            # Create directory structure
            (repo_dir / "src").mkdir()
            (repo_dir / "docs").mkdir()
            (repo_dir / "build").mkdir()

            # Create test files
            (repo_dir / "src" / "main.py").write_text("print('main')")
            (repo_dir / "src" / "utils.py").write_text("print('utils')")
            (repo_dir / "docs" / "README.md").write_text("# Documentation")
            (repo_dir / "build" / "output.log").write_text("build output")
            
            (repo_dir / ".gitignore").write_text("build/\n*.log")

            yield repo_dir

    @pytest.fixture
    def mock_profile_manager(self):
        """Fixture for creating a mock ProfileManager."""
        return Mock(spec=ProfileManager)

    def test_logging_setup(self, capsys):
        """Test logging setup in different verbosity modes."""
        # Verbose mode
        setup_logging(True)
        import logging
        logger = logging.getLogger()
        assert logger.level == logging.DEBUG

        # Non-verbose mode
        setup_logging(False)
        assert logger.level == logging.WARNING

    def test_main_no_arguments(self, monkeypatch):
        """Test main function when no arguments are provided."""
        # Mock sys.argv and parse_args to prevent actual parsing
        with patch('sys.argv', ['reposcope']):
            with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                with patch('reposcope.cli.handle_scan') as mock_handle_scan:
                    # Simulate parsing arguments
                    mock_parse.return_value = Mock(command='scan', verbose=False)
                    
                    # Call main
                    main()
                    
                    # Verify that scan was called with inserted 'scan' argument
                    mock_parse.assert_called_once()
                    mock_handle_scan.assert_called_once()

    def test_main_mixed_arguments(self, monkeypatch):
        """Test main function with mixed/unknown arguments."""
        test_cases = [
            # Unknown first argument should insert 'scan'
            ['reposcope', '-g'],
            ['reposcope', '--output', 'custom.txt'],
            ['reposcope', '-x', '*.log'],
        ]

        for argv in test_cases:
            with patch('sys.argv', argv):
                with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                    with patch('reposcope.cli.handle_scan') as mock_handle_scan:
                        # Simulate parsing arguments
                        mock_parse.return_value = Mock(command='scan', verbose=False)
                        
                        # Call main
                        main()
                        
                        # Verify that scan was called with inserted argument
                        mock_parse.assert_called_once()
                        mock_handle_scan.assert_called_once()

    def test_handle_scan_error_handling(self, mock_profile_manager, temp_repo):
        """Test error handling in handle_scan function."""
        # Prepare arguments
        args = Mock(
            dir=str(temp_repo),
            output='context.txt',
            profile=None,
            use_gitignore=False,
            include=None,
            include_file=None,
            ignore=None,
            ignore_file=None
        )

        # Simulate an error in file generation
        with patch('reposcope.core.RepoScope.generate_context_file') as mock_generate:
            mock_generate.side_effect = Exception("Test error")
            
            with pytest.raises(SystemExit):
                handle_scan(args, mock_profile_manager)

    def test_handle_profile_error_handling(self, mock_profile_manager):
        """Test error handling in handle_profile function."""
        # Simulate various profile errors
        error_test_cases = [
            # Create profile that already exists
            {
                'action': 'create', 
                'name': 'duplicate_profile', 
                'mode': 'include',
                'error': ProfileError("Profile already exists")
            },
            # Delete non-existent profile
            {
                'action': 'delete', 
                'name': 'non_existent', 
                'error': ProfileError("Profile not found")
            },
            # Add patterns to non-existent profile
            {
                'action': 'add', 
                'name': 'non_existent', 
                'patterns': ['*.py'], 
                'error': ProfileError("Profile not found")
            }
        ]

        for case in error_test_cases:
            # Prepare mock arguments
            args = Mock(
                action=case['action'],
                name=case.get('name'),
                patterns=case.get('patterns', []),
                mode=case.get('mode')
            )

            # Configure mock to raise the specific error
            mock_profile_manager.create.side_effect = case['error']
            mock_profile_manager.delete.side_effect = case['error']
            mock_profile_manager.add_patterns.side_effect = case['error']

            # Test that the error is logged and system exits
            with pytest.raises(SystemExit):
                handle_profile(args, mock_profile_manager)

    @pytest.mark.parametrize("mode", ["include", "exclude"])
    def test_handle_profile_commands(self, mock_profile_manager, mode):
        """
        Test 'create', 'delete', 'add', 'remove' subcommands in handle_profile
        by letting the real parser set up the arguments.
        """
        from reposcope.cli import setup_parser

        test_cases = [
            {
                "action": "create",
                "setup_method": "create",
                "cli_args": ["profile", "create", "test_profile", "--mode", mode],
                "expect_call": ("test_profile", mode),
                "output_check": f"Created profile: test_profile ({mode}, 0 patterns)"
            },
            {
                "action": "delete",
                "setup_method": "delete",
                "cli_args": ["profile", "delete", "test_profile"],
                "expect_call": ("test_profile",),
                "output_check": "Deleted profile: test_profile"
            },
            {
                "action": "add",
                "setup_method": "add_patterns",
                "cli_args": ["profile", "add", "test_profile", "*.py", "src/"],
                "expect_call": ("test_profile", ["*.py", "src/"]),
                "output_check": "Added to test_profile:"
            },
            {
                "action": "remove",
                "setup_method": "remove_patterns",
                "cli_args": ["profile", "remove", "test_profile", "*.log"],
                "expect_call": ("test_profile", ["*.log"]),
                "output_check": "Removed from test_profile:"
            }
        ]

        for case in test_cases:
            mock_profile_manager.reset_mock()

            # Parse real CLI args so we get the same attribute names/values
            parser = setup_parser()
            parsed_args = parser.parse_args(case["cli_args"])
            setup_method = getattr(mock_profile_manager, case["setup_method"])

            # Mock return values for create/add/remove if needed
            if case["action"] == "create":
                mock_profile = Mock()
                mock_profile.name = "test_profile"
                mock_profile.mode = mode
                mock_profile.summary.return_value = f"test_profile ({mode}, 0 patterns)"
                setup_method.return_value = mock_profile
            elif case["action"] in ["add", "remove"]:
                setup_method.return_value = case["expect_call"][1]  # e.g. ["*.py", "src/"]

            # Invoke handle_profile with actual parsed_args
            with patch("builtins.print") as mock_print:
                handle_profile(parsed_args, mock_profile_manager)

            # Verify the mock method call
            setup_method.assert_called_once_with(*case["expect_call"])

            # Check console output
            assert any(
                case["output_check"] in call[0][0]
                for call in mock_print.call_args_list
            )


@pytest.mark.parametrize("mode,patterns", [
    ('include', ['*.py', 'src/']),
    ('exclude', ['*.log', 'build/'])
])
def test_profile_edge_cases(mode, patterns):
    """Test edge cases for profile creation and manipulation."""
    manager = ProfileManager()

    # Delete profile first if it exists
    try:
        manager.delete(f'test_{mode}_profile')
    except ProfileError:
        # If profile doesn't exist, that's fine
        pass

    # Create profile
    profile = manager.create(f'test_{mode}_profile', mode)
    assert profile.name == f'test_{mode}_profile'
    assert profile.mode == mode
    assert profile.patterns == []

    # Add patterns
    added = manager.add_patterns(profile.name, patterns)
    assert added == patterns
    assert profile.patterns == patterns

    # Attempt to add duplicate patterns
    duplicate_added = manager.add_patterns(profile.name, patterns)
    assert duplicate_added == []

    # Remove patterns
    removed = manager.remove_patterns(profile.name, [patterns[0]])
    assert removed == [patterns[0]]
    assert patterns[1] in profile.patterns

    # Attempt to remove non-existent pattern
    non_exist_removed = manager.remove_patterns(profile.name, ['non_existent'])
    assert non_exist_removed == []

    # Export patterns
    exported = manager.export_patterns(profile.name)
    assert f"{profile.name} ({mode} mode)" in exported

    # Cleanup
    manager.delete(profile.name)
    with pytest.raises(ProfileError):
        manager.get(profile.name)