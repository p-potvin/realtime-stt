import unittest
from unittest.mock import patch, mock_open, call
import subprocess
import os

from vault_sync import is_safe_input, sync_vault_dependencies

class TestVaultSync(unittest.TestCase):

    def test_is_safe_input_valid(self):
        valid_inputs = [
            "folder123",
            "https://github.com/repo.git",
            "main",
            "feature/branch",
            "user@domain.com",
            "folder-name",
            "folder_name",
            "folder.name",
            "a~b+c=d"
        ]
        for item in valid_inputs:
            self.assertTrue(is_safe_input(item), f"Failed for {item}")

    def test_is_safe_input_invalid(self):
        invalid_inputs = [
            "-branch",
            "--branch",
            "",
            "folder with space",
            "folder;rm -rf /",
            "folder|echo hello",
            "folder&echo hello",
            "folder\nhello",
            None
        ]
        for item in invalid_inputs:
            # Note: is_safe_input expects a string, so we skip None or handle it
            if item is None:
                self.assertFalse(is_safe_input(item))
            else:
                self.assertFalse(is_safe_input(item), f"Failed for {item}")

    @patch("vault_sync.os.path.exists")
    @patch("vault_sync.subprocess.run")
    def test_sync_vault_dependencies_add(self, mock_subprocess_run, mock_exists):
        # Setup: VAULT_DEPENDENCIES.txt exists, but folder does not exist
        mock_exists.side_effect = lambda path: True if path == "VAULT_DEPENDENCIES.txt" else False

        mock_file_content = "agents https://github.com/repo.git main\n"
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            sync_vault_dependencies()

        mock_subprocess_run.assert_called_once_with(
            ["git", "submodule", "add", "-b", "main", "--", "https://github.com/repo.git", "agents"],
            check=True
        )

    @patch("vault_sync.os.path.exists")
    @patch("vault_sync.subprocess.run")
    def test_sync_vault_dependencies_update(self, mock_subprocess_run, mock_exists):
        # Setup: both VAULT_DEPENDENCIES.txt and folder exist
        mock_exists.return_value = True

        mock_file_content = "agents https://github.com/repo.git main\n"
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            sync_vault_dependencies()

        mock_subprocess_run.assert_called_once_with(
            ["git", "submodule", "update", "--init", "--remote", "--", "agents"],
            check=True
        )

    @patch("vault_sync.os.path.exists")
    @patch("vault_sync.subprocess.run")
    def test_sync_vault_dependencies_unsafe_input(self, mock_subprocess_run, mock_exists):
        # Setup: VAULT_DEPENDENCIES.txt exists
        mock_exists.return_value = True

        mock_file_content = "agents https://github.com/repo.git -main\n"
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            sync_vault_dependencies()

        # subprocess.run should not be called because '-main' is unsafe
        mock_subprocess_run.assert_not_called()

    @patch("vault_sync.os.path.exists")
    @patch("vault_sync.subprocess.run")
    def test_sync_vault_dependencies_malformed_line(self, mock_subprocess_run, mock_exists):
        # Setup: VAULT_DEPENDENCIES.txt exists
        mock_exists.return_value = True

        mock_file_content = "agents https://github.com/repo.git\n" # Missing branch
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            sync_vault_dependencies()

        # subprocess.run should not be called due to ValueError (unpacking)
        mock_subprocess_run.assert_not_called()

    @patch("vault_sync.os.path.exists")
    def test_sync_vault_dependencies_no_manifest(self, mock_exists):
        mock_exists.return_value = False
        with patch("builtins.open", mock_open()) as mock_file:
            sync_vault_dependencies()
            mock_file.assert_not_called()

    @patch("vault_sync.os.path.exists")
    @patch("vault_sync.subprocess.run")
    def test_sync_vault_dependencies_ignores_comments_and_empty_lines(self, mock_subprocess_run, mock_exists):
        mock_exists.side_effect = lambda path: True if path == "VAULT_DEPENDENCIES.txt" else False

        mock_file_content = "# Comment\n\nagents https://github.com/repo.git main\n"
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            sync_vault_dependencies()

        # Only one valid line
        self.assertEqual(mock_subprocess_run.call_count, 1)

if __name__ == '__main__':
    unittest.main()
