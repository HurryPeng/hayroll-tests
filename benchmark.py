import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def run(command, cwd=None, timeout=30):
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        return False, e.stdout or "", f"timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)


results = {}

root_dir = Path.cwd()

with open("metadata.json") as file:
# with open("metadata-1.json") as file:
    benchmark_metadata = json.load(file)


def process_program(program):
    name = program["name"]
    path = Path(program["path"])
    tests = program["test_files"]
    sub_tests = program.get("sub_test_files", [])
    program_dir = root_dir / "CBench" / path

    print(f"Processing '{name}'")

    program_result = {
        "status": "passed",
        "failed_stage": None,
        "test_results": {},
    }

    def fail(stage, error):
        program_result["status"] = "failed"
        program_result["failed_stage"] = stage
        program_result["error"] = error

    run("make clean", cwd=program_dir)
    success, out, err = run("bear -- make", cwd=program_dir)
    if not success:
        fail("make", err)
        print(f"Finished '{name}' with status: {program_result['status']}")
        return name, program_result

    compile_commands_path = program_dir / "compile_commands.json"
    if not compile_commands_path.exists():
        fail("make", "compile_commands.json not found")
        print(f"Finished '{name}' with status: {program_result['status']}")
        return name, program_result
    # Read compile_commands.json. If it's simply "[]", treat it as failure.
    with compile_commands_path.open() as cc_file:
        cc_content = cc_file.read()
        if cc_content.strip() == "[]":
            fail("make", "compile_commands.json is empty")
            print(f"Finished '{name}' with status: {program_result['status']}")
            return name, program_result

    run("rm -rf ./c2rust_out", cwd=program_dir)
    success, out, err = run(
        "c2rust transpile --emit-build-files compile_commands.json -o c2rust_out",
        # "~/Hayroll/hayroll transpile compile_commands.json -o hayroll_out",
        cwd=program_dir,
        timeout=600,
    )
    if not success:
        fail("transpile", err)
        print(f"Finished '{name}' with status: {program_result['status']}")
        return name, program_result

    cargo_dir = program_dir / "c2rust_out"
    # cargo_dir = program_dir / "hayroll_out"
    success, out, err = run("cargo build", cwd=cargo_dir)
    if not success:
        fail("rust_build", err)
        print(f"Finished '{name}' with status: {program_result['status']}")
        return name, program_result

    for test_file in tests:
        exe_name = Path(test_file).stem + "_exe"
        sources = " ".join([test_file] + sub_tests)
        compile_cmd = (
            f"gcc -o {exe_name} {sources} -Isrc -Lc2rust_out/target/debug -lc2rust_out -ldl -lpthread -lm"
            # f"gcc -o {exe_name} {sources} -Isrc -Lhayroll_out/target/debug -lhayroll_out -ldl -lpthread -lm"
        )
        success, out, err = run(compile_cmd, cwd=program_dir)
        if not success:
            program_result["test_results"][test_file] = {
                "status": "link_failed",
                "error": err,
            }
            program_result["status"] = "failed"
            program_result["failed_stage"] = "link"
            continue

        success, out, err = run(f"./{exe_name}", cwd=program_dir)
        if success:
            program_result["test_results"][test_file] = {"status": "passed"}
        else:
            program_result["test_results"][test_file] = {
                "status": "failed",
                "stdout": out,
                "stderr": err,
            }
            program_result["status"] = "failed"
            program_result["failed_stage"] = "test"

    print(f"Finished '{name}' with status: {program_result['status']}")

    return name, program_result


with ThreadPoolExecutor(max_workers=16) as executor:
    futures = [
        executor.submit(process_program, program)
        for program in benchmark_metadata["programs"]
    ]
    for future in futures:
        name, program_result = future.result()
        results[name] = program_result

with open("benchmark_summary.json", "w") as file:
    json.dump(results, file, indent=4)

print("Finished")
