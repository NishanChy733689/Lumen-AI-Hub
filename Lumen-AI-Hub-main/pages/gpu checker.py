import subprocess

try:
    # Query nvidia-smi for the names of attached GPUs
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True, 
        check=True
    )
    gpus = result.stdout.strip().split("\n")
    print(f"CUDA Device(s) Available: {gpus}")
except (subprocess.CalledProcessError, FileNotFoundError, OSError):
    print("CUDA is NOT available (nvidia-smi command not found or failed).")
