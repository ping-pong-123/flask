import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_command(command, timeout=10):
    try:
        if isinstance(command, str):
            result = subprocess.run(
                command,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout
            )
        else:
            result = subprocess.run(
                command,
                shell=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout
            )

        if result.returncode == 0:
            return (command, True, result.stdout)
        else:
            return (command, False, result.stderr)

    except subprocess.TimeoutExpired:
        return (command, False, f"[Timeout] Command took longer than {timeout} seconds.")
    except Exception as e:
        return (command, False, str(e))


def run_commands_parallel(commands, timeout=10, max_workers=None):
    """
    Run a list of shell commands in parallel with timeout.

    Args:
        commands (list): List of shell commands (strings or lists).
        timeout (int): Timeout in seconds for each command.
        max_workers (int, optional): Max threads to use. Defaults to len(commands).

    Returns:
        list of tuples: Each tuple contains (command, success: bool, output: str)
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers or len(commands)) as executor:
        future_to_cmd = {
            executor.submit(run_command, cmd, timeout): cmd
            for cmd in commands
        }

        for future in as_completed(future_to_cmd):
            result = future.result()
            results.append(result)

    return results



#usage 
#cmd, success, output = run_command("nmap 192.168.0.1", timeout=50)
"""
commands = [
    "nmap 192.168.0.1",
    "nmap 8.8.8.8",
    "sleep 25 && echo done"  # This one should timeout if timeout=5
]
#usage
results = run_commands_parallel(commands, timeout=30)

for cmd, success, output in results:
    print(f"\n--- Command: {cmd} ---")
    print("✅ Success:" if success else "❌ Error:")
    print(output)"""
