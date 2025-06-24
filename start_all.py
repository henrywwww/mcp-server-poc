
import multiprocessing
import subprocess

def run_mcp():
    subprocess.run(["python", "main.py"])

def run_proxy():
    subprocess.run(["uvicorn", "proxy_server:app", "--host", "0.0.0.0", "--port", "8080"])

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_mcp)
    p2 = multiprocessing.Process(target=run_proxy)
    p1.start()
    p2.start()
    p1.join()
    p2.join()
