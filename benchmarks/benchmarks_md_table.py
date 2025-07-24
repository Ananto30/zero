import os
import re

available_benchmarks = [
    "benchmark-aiohttp",
    "benchmark-aiozmq",
    "benchmark-blacksheep",
    "benchmark-fastapi",
    "benchmark-sanic",
    "benchmark-zero",
]


def get_latest_history():
    # file format is `<available_benchmark>__<date>.log`
    history_dir = "dockerize/history"
    if not os.path.exists(history_dir):
        return []
    files = os.listdir(history_dir)
    files = [f for f in files if f.endswith(".log")]

    latest_files = {}
    for f in files:
        benchmark_name = f.split("__")[0]
        if benchmark_name in available_benchmarks:
            date_str = f.split("__")[1].replace(".log", "")
            if (
                benchmark_name not in latest_files
                or date_str > latest_files[benchmark_name]
            ):
                latest_files[benchmark_name] = date_str

    return [f"{benchmark}__{date}.log" for benchmark, date in latest_files.items()]


def parse_benchmark_log(filepath):
    results = []
    current_test = None
    latency_99 = None
    requests_sec = None

    # Patterns to identify test type and metrics
    test_type_pattern = re.compile(r"Running 30s test @ http://gateway:8000/(\w+_?\w*)")
    latency_pattern = re.compile(r"99%\s+([\d.]+)ms")
    req_sec_pattern = re.compile(r"Requests/sec:\s+([\d.]+)")

    with open(filepath, "r") as f:
        for line in f:
            # Identify the test type
            match_test = test_type_pattern.search(line)
            if match_test:
                current_test = match_test.group(1)
                continue

            # Find 99% latency
            match_99 = latency_pattern.search(line)
            if match_99:
                latency_99 = float(match_99.group(1))
                continue

            # Find Requests/sec
            match_req = req_sec_pattern.search(line)
            if match_req and current_test:
                requests_sec = float(match_req.group(1))
                results.append(
                    {
                        "test": current_test,
                        "99%_latency_ms": latency_99,
                        "requests_per_sec": requests_sec,
                    }
                )
                # Reset for next run
                current_test = None
                latency_99 = None
                requests_sec = None

    return results


def make_comparison_table(all_results):
    # Map: framework -> { "hello": {...}, "order": {...}, "async_hello": {...}, "async_order": {...} }
    framework_map = {
        "aiohttp": "aiohttp",
        "aiozmq": "aiozmq",
        "blacksheep": "blacksheep",
        "fastapi": "fastApi",
        "sanic": "sanic",
        "zero": "zero(sync)",
        "zero-async": "zero(async)",
    }
    # Prepare a dict to collect results
    table_data = {fw: {} for fw in framework_map.values()}

    # Helper to match test names to columns
    def classify(framework, test):
        if framework == "zero":
            if test == "hello":
                return "zero(sync)", "hello"
            elif test == "order":
                return "zero(sync)", "order"
            elif test == "async_hello":
                return "zero(async)", "hello"
            elif test == "async_order":
                return "zero(async)", "order"
        else:
            if test == "hello":
                return framework_map[framework], "hello"
            elif test == "order":
                return framework_map[framework], "order"
        return None, None

    for benchmark, results in all_results.items():
        framework = benchmark.replace("benchmark-", "")
        for result in results:
            fw, col = classify(framework, result["test"])
            if fw and col:
                table_data[fw][col] = result

    header = (
        '| Framework   | "hello world" (req/s) | 99% latency (ms) | redis save (req/s) | 99% latency (ms) |\n'
        "| ----------- | --------------------- | ---------------- | ------------------ | ---------------- |"
    )
    rows = []
    for fw in [
        "aiohttp",
        "aiozmq",
        "blacksheep",
        "fastApi",
        "sanic",
        "zero(sync)",
        "zero(async)",
    ]:
        hello = table_data[fw].get("hello", {})
        order = table_data[fw].get("order", {})
        row = (
            f"| {fw:<11} | "
            f"{hello.get('requests_per_sec', ''):<21} | {hello.get('99%_latency_ms', ''):<16} | "
            f"{order.get('requests_per_sec', ''):<18} | {order.get('99%_latency_ms', ''):<16} |"
        )
        rows.append(row)
    return header + "\n" + "\n".join(rows)


if __name__ == "__main__":
    history_files = get_latest_history()
    all_results = {}
    for history_file in history_files:
        filepath = os.path.join("dockerize/history", history_file)
        if os.path.exists(filepath):
            benchmark_name = history_file.split("__")[0]
            results = parse_benchmark_log(filepath)
            all_results[benchmark_name] = results
    comparison_table = make_comparison_table(all_results)
    print(comparison_table)
