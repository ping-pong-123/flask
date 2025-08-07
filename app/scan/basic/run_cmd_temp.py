import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_command(template, variables, timeout=10):
    try:
        command = template.format(**variables)  # Format the command with custom values
        result = subprocess.run(command, shell=True, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=timeout)
        if result.returncode == 0:
            return (command, True, result.stdout)
        else:
            return (command, False, result.stderr)
    except subprocess.TimeoutExpired:
        return (template, False, f"[Timeout] Command exceeded {timeout} seconds.")
    except Exception as e:
        return (template, False, str(e))

def run_commands_parallel(command_data_list, timeout=10, max_workers=None):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers or len(command_data_list)) as executor:
        futures = [
            executor.submit(run_command, cmd_data["template"], cmd_data["vars"], timeout)
            for cmd_data in command_data_list
        ]
        for future in as_completed(futures):
            results.append(future.result())
    return results

link="https://google.com"
commands_to_run = [
    {"template": "nmap {target}", "vars": {"target": "192.168.0.1"}},
    {"template": "curl -I {url}", "vars": {"url": link}},
    {"template": "ping -c {count} {host}", "vars": {"host": "8.8.8.8", "count": "5"}}
]

results = run_commands_parallel(commands_to_run, timeout=20)

for cmd, success, output in results:
    print(f"\n--- Command: {cmd} ---")
    print("✅ Success:" if success else "❌ Error:")
    print(output)


# Define the template and variables
template = "nmap {target}"
variables = {"target": "192.168.0.1"}

# Call the function
command, success, output = run_command(template, variables, timeout=20)

# Print result
print(f"Command: {command}")
print("✅ Success:" if success else "❌ Error:")
print(output)