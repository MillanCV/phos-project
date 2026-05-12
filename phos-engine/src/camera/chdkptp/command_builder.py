from __future__ import annotations


def build_exec_command(chdkptp_bin: str, commands: list[str]) -> list[str]:
    command = [chdkptp_bin]
    for item in commands:
        command.append(f"-e{item}")
    return command
