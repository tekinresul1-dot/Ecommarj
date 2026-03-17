import pexpect
import sys

IP = "91.98.226.158"
PASSWORD = "UUXp7dgud7UF"
COMMAND = "ls -al /root/Ecommarj || ls -al /var/www/Ecommarj || ls -al /opt/Ecommarj || find / -name docker-compose.yml -maxdepth 4"

child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no root@{IP} "{COMMAND}"', encoding='utf-8')
child.logfile = sys.stdout

try:
    i = child.expect(['[P|p]assword:', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
    if i == 0:
        child.sendline(PASSWORD)
        child.expect(pexpect.EOF, timeout=60)
except Exception as e:
    print(f"Error: {e}")

child.close()
