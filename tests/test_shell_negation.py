import pytest
import tempfile
import subprocess
import os
import sys
from pathlib import Path


@pytest.fixture
def temp_repo():
    """Create a temporary repository with files for testing shell negation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir)
        
        # Create directory structure
        (repo_dir / "src").mkdir()
        (repo_dir / "docs").mkdir()
        (repo_dir / "tests").mkdir()
        
        # Create test files
        (repo_dir / "src/main.py").write_text("main file")
        (repo_dir / "src/utils.py").write_text("utilities")
        (repo_dir / "src/config.py").write_text("configuration")
        
        (repo_dir / "docs/readme.md").write_text("readme")
        (repo_dir / "docs/setup.md").write_text("setup guide")
        (repo_dir / "docs/api.md").write_text("api documentation")
        
        (repo_dir / "tests/test_main.py").write_text("test main")
        (repo_dir / "tests/test_utils.py").write_text("test utils")
        
        (repo_dir / "setup.py").write_text("setup code")
        (repo_dir / "README.md").write_text("main readme")
        (repo_dir / "LICENSE").write_text("license info")
        
        yield repo_dir


def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Running command: {cmd}")
    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        cwd=cwd
    )
    
    if process.returncode != 0:
        print(f"Command failed with code {process.returncode}")
        print(f"STDOUT: {process.stdout}")
        print(f"STDERR: {process.stderr}")
    
    return process


def get_files_from_output(output_file):
    """Parse the context file and return a set of files included."""
    try:
        with open(output_file, "r") as f:
            content = f.read()
        
        # Extract files from the "File Tree:" section
        file_tree_section = content.split("File Tree:")[1].split("File Contents:")[0]
        files = set()
        for line in file_tree_section.strip().split("\n"):
            if line.startswith("└── "):
                files.add(line[4:])  # Remove the "└── " prefix
        return files
    except (FileNotFoundError, IndexError) as e:
        print(f"Error reading output file: {e}")
        return set()


class TestNegationInCore:
    """Test negation patterns directly using the RepoScope API."""
    
    def test_negation_via_api(self, temp_repo):
        """Test negation patterns work correctly via direct API calls."""
        from reposcope.core import RepoScope
        
        # Test excluding all .py files but including test_*.py
        scope = RepoScope(temp_repo)
        scope.use_ignore_patterns(["*.py", "!test_*.py"])
        
        files = set(str(f.relative_to(temp_repo)) for f in scope.collect_files())
        
        # Should exclude regular .py files
        assert "src/main.py" not in files
        assert "src/utils.py" not in files
        assert "setup.py" not in files
        
        # But include test_*.py files due to negation
        assert "tests/test_main.py" in files
        assert "tests/test_utils.py" in files
    
    def test_multiple_negations_api(self, temp_repo):
        """Test multiple negation patterns with different orders."""
        from reposcope.core import RepoScope
        
        # Test more complex pattern combinations
        scope = RepoScope(temp_repo)
        scope.use_ignore_patterns(["*.py", "*.md", "!test_*.py", "!README.md"])
        
        files = set(str(f.relative_to(temp_repo)) for f in scope.collect_files())
        
        # Should include the negated files
        assert "tests/test_main.py" in files
        assert "tests/test_utils.py" in files
        assert "README.md" in files
        
        # Should exclude non-negated files
        assert "src/main.py" not in files
        assert "docs/api.md" not in files
    
    def test_negation_in_include_mode_api(self, temp_repo):
        """Test negation in include mode via API."""
        from reposcope.core import RepoScope
        
        # Include .py files but exclude config.py
        scope = RepoScope(temp_repo)
        scope.use_include_patterns(["*.py", "!src/config.py"])
        
        files = set(str(f.relative_to(temp_repo)) for f in scope.collect_files())
        
        # Should include most .py files
        assert "src/main.py" in files
        assert "src/utils.py" in files
        assert "tests/test_main.py" in files
        
        # Should exclude config.py due to negation
        assert "src/config.py" not in files


class TestNegationInCLI:
    """
    Test negation patterns via CLI without actual shell escaping.
    This tests the CLI parsing logic directly.
    """
    
    def test_negation_via_cli_args(self, temp_repo):
        """Test negation using CLI arguments directly."""
        output_file = temp_repo / "context.txt"
        
        # Build command with arguments as separate list items to avoid shell escaping issues
        cmd = [
            sys.executable, "-m", "reposcope", "scan",
            "-o", str(output_file),
            "-x", "*.py", "!test_*.py"
        ]
        
        process = run_command(cmd, temp_repo)
        assert process.returncode == 0, f"Process failed: {process.stderr}"
        
        files = get_files_from_output(output_file)
        
        # Should exclude regular .py files
        assert "src/main.py" not in files
        assert "src/utils.py" not in files
        assert "setup.py" not in files
        
        # But include test_*.py files due to negation
        assert "tests/test_main.py" in files
        assert "tests/test_utils.py" in files
    
    def test_include_mode_cli_args(self, temp_repo):
        """Test negation in include mode with CLI args."""
        output_file = temp_repo / "context.txt"
        
        # Include .py files but exclude config.py
        cmd = [
            sys.executable, "-m", "reposcope", "scan",
            "-o", str(output_file),
            "-i", "*.py", "!src/config.py"
        ]
        
        process = run_command(cmd, temp_repo)
        assert process.returncode == 0, f"Process failed: {process.stderr}"
        
        files = get_files_from_output(output_file)
        
        # Should include most .py files
        assert "src/main.py" in files
        assert "src/utils.py" in files
        assert "tests/test_main.py" in files
        
        # Should exclude config.py due to negation
        assert "src/config.py" not in files
        
        # Should exclude non-py files
        assert "README.md" not in files


# Only run this class if the shell escaping tests should be run
@pytest.mark.shell
class TestNegationViaShell:
    """Test actual shell escaping with negation patterns."""
    
    def test_shell_quoting(self, temp_repo):
        """Test shell quoting for negation patterns."""
        output_file = temp_repo / "context.txt"
        
        # Use shell=True with appropriate quoting
        cmd = f"{sys.executable} -m reposcope scan -o {output_file} -x '*.py' '!test_*.py'"
        
        process = subprocess.run(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            cwd=str(temp_repo)
        )
        
        assert process.returncode == 0, f"Process failed: {process.stderr}"
        
        files = get_files_from_output(output_file)
        
        # Should exclude regular .py files
        assert "src/main.py" not in files
        assert "src/utils.py" not in files
        
        # But include test_*.py files due to negation
        assert "tests/test_main.py" in files
        assert "tests/test_utils.py" in files


if __name__ == "__main__":
    pytest.main()
