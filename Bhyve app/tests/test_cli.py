from __future__ import annotations

import unittest

import main


class CliParsingTests(unittest.TestCase):
    def test_empty_invocation_defaults_to_run(self) -> None:
        parser = main.build_parser()
        args = parser.parse_args(main.normalize_cli_args([]))
        self.assertEqual(args.command, "run")
        self.assertFalse(args.once)
        self.assertFalse(args.dry_run)

    def test_config_after_subcommand_is_normalized(self) -> None:
        parser = main.build_parser()
        args = parser.parse_args(
            main.normalize_cli_args(["run", "--config", "config.json"])
        )
        self.assertEqual(args.command, "run")
        self.assertEqual(str(args.config), "config.json")

    def test_config_before_subcommand_still_parses(self) -> None:
        parser = main.build_parser()
        args = parser.parse_args(
            main.normalize_cli_args(["--config", "config.json", "run"])
        )
        self.assertEqual(args.command, "run")
        self.assertEqual(str(args.config), "config.json")

    def test_web_command_parses(self) -> None:
        parser = main.build_parser()
        args = parser.parse_args(
            main.normalize_cli_args(["--config", "config.json", "web", "--port", "8787"])
        )
        self.assertEqual(args.command, "web")
        self.assertEqual(args.port, 8787)
        self.assertEqual(str(args.config), "config.json")


if __name__ == "__main__":
    unittest.main()