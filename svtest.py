import os
import subprocess
import time
import re
import csv
from datetime import datetime

iqcapture_path = r"C:/Users/AWCC/Downloads/RSA_API-master/RSA_API-master/Utilities/RSA_API Apps V3.11/Apps/x64/IQcapture.exe"

# シリアル番号とデバイスIDを取得・記録するための配列
device_serial_mapping = {
    "B021101": None,
    "B021110": None,
}

# 処理リスト
tasks = [
    ("dev={B021110} cf=5190e6 bw=40e6 dest=2 fn=iqstream_5170-5210_B021110 msec=60000", "dev={B021101} cf=922.5e6 bw=15e6 dest=2 fn=iqstream_915-930_B021101 msec=60000"),
    ("dev={B021110} cf=5230e6 bw=40e6 dest=2 fn=iqstream_5210-5250_B021110 msec=60000", "dev={B021101} cf=2417.5e6 bw=35e6 dest=2 fn=iqstream_2400-2435_B021101 msec=60000"),
    ("dev={B021110} cf=5270e6 bw=40e6 dest=2 fn=iqstream_5250-5290_B021110 msec=60000", "dev={B021101} cf=2450e6 bw=30e6 dest=2 fn=iqstream_2435-2465_B021101 msec=60000"),
    ("dev={B021110} cf=5310e6 bw=40e6 dest=2 fn=iqstream_5290-5330_B021110 msec=60000", "dev={B021101} cf=2482.5e6 bw=35e6 dest=2 fn=iqstream_2465-2500_B021101 msec=60000"),
    ("dev={B021110} cf=5505e6 bw=30e6 dest=2 fn=iqstream_5490-5520_B021110 msec=60000", ""),
    ("dev={B021110} cf=5540e6 bw=40e6 dest=2 fn=iqstream_5520-5560_B021110 msec=60000", ""),
    ("dev={B021110} cf=5580e6 bw=40e6 dest=2 fn=iqstream_5560-5600_B021110 msec=60000", ""),
    ("dev={B021110} cf=5620e6 bw=40e6 dest=2 fn=iqstream_5600-5640_B021110 msec=60000", ""),
    ("dev={B021110} cf=5660e6 bw=40e6 dest=2 fn=iqstream_5640-5680_B021110 msec=60000", ""),
    ("dev={B021110} cf=5695e6 bw=30e6 dest=2 fn=iqstream_5680-5710_B021110 msec=60000", ""),
]

# CSVファイルのパス
csv_file_path = "execution_result.csv"

# 実行時に保存されるファイルのディレクトリ
output_directory = os.getcwd()  # 実行フォルダ

def get_device_mapping():
    try:
        result = subprocess.run([iqcapture_path], capture_output=True, text=True, shell=True)
        output = result.stdout
        pattern = r"Dev:(\d+)\s+ID:(\d+)\s+S/N:\"(\w+)\""
        matches = re.findall(pattern, output)

        for dev, _, serial in matches:
            if serial in device_serial_mapping:
                device_serial_mapping[serial] = dev

        print(f"devs: {device_serial_mapping}")
    except Exception as e:
        print(f"errr: {e}")

def process_task(B021110_args, B021101_args, task_idx, times_B021110, times_B021101, sizes_B021110, sizes_B021101):
    processes = []

    if B021110_args:
        B021110_args = B021110_args.format(**device_serial_mapping)
        #print(f"strt: B021110 {idx+1}")#{B021110_args}")
        start_time = time.time()
        process = subprocess.Popen(
            [iqcapture_path] + B021110_args.split(),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        processes.append((process, start_time, task_idx, "B021110", B021110_args))

    if B021101_args:
        B021101_args = B021101_args.format(**device_serial_mapping)
        #print(f"strt: B021101 {idx+1}")#{B021101_args}")
        start_time = time.time()
        process = subprocess.Popen(
            [iqcapture_path] + B021101_args.split(),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        processes.append((process, start_time, task_idx, "B021101", B021101_args))

    for process, start_time, idx, device, args in processes:
        process.wait()
        elapsed_time = time.time() - start_time
        filename = re.search(r"fn=(\S+)", args).group(1) + ".tiq"
        file_path = os.path.join(output_directory, filename)

        if device == "B021110":
            times_B021110[idx] = elapsed_time
            sizes_B021110[idx] = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        elif device == "B021101":
            times_B021101[idx] = elapsed_time
            sizes_B021101[idx] = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        print(f"        msrd: {device} {idx+1}\n               TIME: {elapsed_time:.2f}[s]\n               SIZE: {sizes_B021110[idx] if device == 'B021110' else sizes_B021101[idx]}[byte]")

def run_tasks():
    times_B021110 = [0] * 10
    times_B021101 = [0] * 10
    sizes_B021110 = [0] * 10
    sizes_B021101 = [0] * 10
    start_time = time.time()

    for idx, (B021110_args, B021101_args) in enumerate(tasks):
        process_task(B021110_args, B021101_args, idx, times_B021110, times_B021101, sizes_B021110, sizes_B021101)
        time.sleep(1)

    total_elapsed_time = time.time() - start_time
    execution_time = {
        "実行時刻": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "全体実行時間": total_elapsed_time,
        **{f"time_B021101_{i+1}": times_B021101[i] for i in range(10)},
        **{f"time_B021110_{i+1}": times_B021110[i] for i in range(10)},
        **{f"size_B021101_{i+1}": sizes_B021101[i] for i in range(10)},
        **{f"size_B021110_{i+1}": sizes_B021110[i] for i in range(10)},
    }

    write_to_csv(execution_time)

def write_to_csv(execution_time):
    header = ["実行時刻", "全体実行時間"] + \
             [f"time_B021101_{i+1}" for i in range(10)] + \
             [f"time_B021110_{i+1}" for i in range(10)] + \
             [f"size_B021101_{i+1}" for i in range(10)] + \
             [f"size_B021110_{i+1}" for i in range(10)]
    file_exists = False

    try:
        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as f:
            file_exists = True
    except FileNotFoundError:
        pass

    with open(csv_file_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)

        if not file_exists:
            writer.writeheader()

        writer.writerow(execution_time)

if __name__ == "__main__":
    print(f"strt: init")
    get_device_mapping()
    if None in device_serial_mapping.values():
        print(f"errr: init")
        print(f"errr: デバイスIDが正しく取得できませんでした。USBケーブルの再接続や充電ケーブルの接続を試してください。")
    else:
        print(f"cmpl: init")
        print(f"strt: meas")
        for i in range(3):
            print(f"    meas: {i+1}")
            run_tasks()
        print(f"cmpl: meas")
