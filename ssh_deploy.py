import pexpect
import sys
import time

IP = "91.98.226.158"
PASSWORD = "UUXp7dgud7UF"
COMMAND = "apt update && apt upgrade -y && apt install git nginx certbot python3-certbot-nginx -y"

print(f"Connecting to {IP}...")
child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no root@{IP} "{COMMAND}"', encoding='utf-8')
child.logfile = sys.stdout

try:
    i = child.expect(['assword:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
    if i == 0:
        child.sendline(PASSWORD)
        child.expect(pexpect.EOF, timeout=600)
    elif i == 1:
        print("Done without password prompt (maybe key auth?)")
    elif i == 2:
        print("Timeout waiting for password prompt")
except Exception as e:
    print(f"Error: {e}")

child.close()
print(f"Exit status: {child.exitstatus}")
