import pytest
import os
import logging
from pathlib import Path
import tempfile
import shutil
from reposcope.core import RepoScope
from reposcope.cli import main
import sys
from unittest.mock import patch

@pytest.fixture
def temp_repo():
    """Create a temporary repository with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir)
        
        # Create directory structure
        (repo_dir / "src").mkdir()
        (repo_dir / "docs").mkdir()
        (repo_dir / "tests").mkdir()
        (repo_dir / "build").mkdir()
        (repo_dir / ".git").mkdir()
        (repo_dir / "__pycache__").mkdir()
        
        # Create test files
        (repo_dir / "src" / "main.py").write_text("print('main')")
        (repo_dir / "src" / "utils.py").write_text("print('utils')")
        (repo_dir / "docs" / "README.md").write_text("# Documentation")
        (repo_dir / "tests" / "test_main.py").write_text("def test_main(): pass")
        (repo_dir / "build" / "output.txt").write_text("build output")
        (repo_dir / "__pycache__" / "main.cpython-39.pyc").write_text("cached")
        (repo_dir / ".gitignore").write_text("\n".join([
            "build/",
            "__pycache__/",
            "*.pyc",
        ]))
        
        yield repo_dir

@pytest.fixture
def temp_ignore_file():
    """Create a temporary ignore file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("\n".join([
            "tests/",
            "*.md",
        ]))
        return Path(f.name)

def test_gitignore_basic(temp_repo):
    """Test basic .gitignore functionality."""
    scope = RepoScope(temp_repo)
    scope.use_gitignore()
    files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
    
    # Should include
    assert "src/main.py" in files
    assert "src/utils.py" in files
    assert "docs/README.md" in files
    
    # Should exclude
    assert "build/output.txt" not in files
    assert "__pycache__/main.cpython-39.pyc" not in files

def test_extra_ignore_file(temp_repo, temp_ignore_file):
    """Test using an additional ignore file."""
    scope = RepoScope(temp_repo)
    scope.use_ignore_file(str(temp_ignore_file))
    files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
    
    # Should include
    assert "src/main.py" in files
    assert "src/utils.py" in files
    
    # Should exclude based on ignore file
    assert "tests/test_main.py" not in files
    assert "docs/README.md" not in files

def test_command_line_ignore(temp_repo):
    """Test ignore patterns from command line."""
    scope = RepoScope(temp_repo)
    scope.use_ignore_patterns(["*.py", "docs/"])
    files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
    
    # Should exclude
    assert "src/main.py" not in files
    assert "docs/README.md" not in files
    
    # Should include
    assert "build/output.txt" in files

def test_include_patterns(temp_repo):
    """Test include patterns."""
    scope = RepoScope(temp_repo)
    scope.use_include_patterns(["src/*.py"])
    files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
    
    # Should include only Python files in src
    assert "src/main.py" in files
    assert "src/utils.py" in files
    
    # Should exclude everything else
    assert "docs/README.md" not in files
    assert "tests/test_main.py" not in files
    assert "build/output.txt" not in files

def test_include_file(temp_repo):
    """Test include patterns from file."""
    include_file = temp_repo / "include.txt"
    include_file.write_text("src/*.py\ndocs/*.md")
    
    scope = RepoScope(temp_repo)
    scope.use_include_file(str(include_file))
    files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
    
    # Should include only specified patterns
    assert "src/main.py" in files
    assert "docs/README.md" in files
    
    # Should exclude everything else
    assert "tests/test_main.py" not in files
    assert "build/output.txt" not in files

def test_combining_gitignore_and_extra_ignore(temp_repo, temp_ignore_file):
    """Test combining .gitignore and extra ignore file."""
    scope = RepoScope(temp_repo)
    scope.use_gitignore()
    scope.use_ignore_file(str(temp_ignore_file))
    files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
    
    # Should exclude from both .gitignore and extra ignore
    assert "build/output.txt" not in files  # from .gitignore
    assert "docs/README.md" not in files    # from extra ignore
    assert "tests/test_main.py" not in files  # from extra ignore

def test_include_overrides_ignore(temp_repo):
    """Test that include mode overrides any ignore patterns."""
    scope = RepoScope(temp_repo)
    scope.use_gitignore()  # This should be ignored once we switch to include mode
    scope.use_include_patterns(["build/*"])  # This should take precedence
    files = {str(f.relative_to(temp_repo)) for f in scope.collect_files()}
    
    # Should include only build files, despite being in .gitignore
    assert "build/output.txt" in files
    assert len(files) == 1

def test_nonexistent_files(temp_repo):
    """Test handling of nonexistent ignore/include files."""
    scope = RepoScope(temp_repo)
    
    # Test ignore mode with nonexistent file
    scope.use_ignore_file("nonexistent.txt")
    files_ignore = scope.collect_files()
    # In ignore mode with no patterns, should include all files
    assert len(files_ignore) > 0
    
    # Create new scope for include mode test
    scope = RepoScope(temp_repo)
    scope.use_include_file("also_nonexistent.txt")
    files_include = scope.collect_files()
    # In include mode with no patterns, should include no files
    assert len(files_include) == 0

def test_empty_patterns(temp_repo):
    """Test handling of empty pattern lists."""
    scope = RepoScope(temp_repo)
    
    # Empty ignore patterns should include everything
    scope.use_ignore_patterns([])
    files1 = set(scope.collect_files())
    assert len(files1) > 0
    
    # Empty include patterns should include nothing
    scope.use_include_patterns([])
    files2 = set(scope.collect_files())
    assert len(files2) == 0

def test_cli_short_arguments(temp_repo, capsys):
    """Test CLI with short argument versions."""
    # Save current working directory
    original_cwd = os.getcwd()
    try:
        # Change to temp_repo directory for tests
        os.chdir(temp_repo)

        # Test -g (--use-gitignore)
        with patch.object(sys, 'argv', ['reposcope', '-g']):
            main()
            captured = capsys.readouterr()
            assert "Generated context file: context.txt" in captured.out

        # Test -i (--include)
        with patch.object(sys, 'argv', ['reposcope', '-i', '*.py']):
            main()
            captured = capsys.readouterr()
            assert "Generated context file: context.txt" in captured.out

        # Test -o (--output)
        output_file = "test_output.txt"
        with patch.object(sys, 'argv', ['reposcope', '-g', '-o', output_file]):
            main()
            captured = capsys.readouterr()
            assert f"Generated context file: {output_file}" in captured.out
            assert os.path.exists(output_file)

        # Test -v (--verbose)
        with patch.object(sys, 'argv', ['reposcope', '-g', '-v']):
            main()
            captured = capsys.readouterr()
            assert "DEBUG" in captured.err  # Check for debug output in stderr

        # Test -d (--dir)
        with patch.object(sys, 'argv', ['reposcope', '-d', str(temp_repo), '-g']):
            main()
            captured = capsys.readouterr()
            assert "Generated context file: context.txt" in captured.out

        # Test -X (--exclude-file/--ignore-file)
        ignore_file = temp_repo / "custom_ignore.txt"
        ignore_file.write_text("*.pyc")
        with patch.object(sys, 'argv', ['reposcope', '-X', str(ignore_file)]):
            main()
            captured = capsys.readouterr()
            assert "Generated context file: context.txt" in captured.out

        # Test -x (--exclude/--ignore)
        with patch.object(sys, 'argv', ['reposcope', '-x', '*.pyc', '*.pyo']):
            main()
            captured = capsys.readouterr()
            assert "Generated context file: context.txt" in captured.out

        # Test -I (--include-file)
        include_file = temp_repo / "include.txt"
        include_file.write_text("*.py")
        with patch.object(sys, 'argv', ['reposcope', '-I', str(include_file)]):
            main()
            captured = capsys.readouterr()
            assert "Generated context file: context.txt" in captured.out

    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_cli_aliases(temp_repo, capsys):
    """Test command line argument aliases."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_repo)

        # Test --exclude alias for --ignore
        with patch.object(sys, 'argv', ['reposcope', '--exclude', '*.pyc']):
            main()
            captured = capsys.readouterr()
            assert "Generated context file: context.txt" in captured.out

        # Test --exclude-file alias for --ignore-file
        ignore_file = temp_repo / "custom_ignore.txt"
        ignore_file.write_text("*.pyc")
        with patch.object(sys, 'argv', ['reposcope', '--exclude-file', str(ignore_file)]):
            main()
            captured = capsys.readouterr()
            assert "Generated context file: context.txt" in captured.out

    finally:
        os.chdir(original_cwd)

def test_cli_mixed_arguments(temp_repo, capsys):
    """Test mixing different argument versions."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_repo)

        # Mix short and long arguments
        with patch.object(sys, 'argv', ['reposcope', '-g', '--output', 'out.txt']):
            main()
            captured = capsys.readouterr()
            assert "Generated context file: out.txt" in captured.out

        # Mix exclude and ignore
        with patch.object(sys, 'argv', ['reposcope', '--exclude', '*.pyc', '--ignore', '*.pyo']):
            main()
            captured = capsys.readouterr()
            assert "Generated context file: context.txt" in captured.out

        # Mix verbose with different argument styles
        with patch.object(sys, 'argv', ['reposcope', '--use-gitignore', '-v']):
            main()
            captured = capsys.readouterr()
            assert "DEBUG" in captured.err

    finally:
        os.chdir(original_cwd)