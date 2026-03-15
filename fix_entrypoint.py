import re

entry_path = '/var/www/ecommarj/backend/entrypoint.sh'
with open(entry_path, 'r') as f:
    content = f.read()

# Remove the while loop for PostgreSQL wait
content = re.sub(r'echo "⏳ PostgreSQL bekleniyor\.\.\."\s*while ! nc -z \$POSTGRES_HOST \$POSTGRES_PORT; do[\s\S]*?done\s*echo "✅ PostgreSQL hazır!"', '', content)

# Fallback: if re.sub failed, just replace the lines
if "while ! nc -z" in content:
    lines = content.split('\n')
    new_lines = []
    skip = False
    for line in lines:
        if 'PostgreSQL bekleniyor' in line or 'while ! nc -z' in line:
            skip = True
            continue
        if skip and ('done' in line or 'PostgreSQL hazır' in line):
            skip = False
            continue
        if not skip:
            new_lines.append(line)
    content = '\n'.join(new_lines)

with open(entry_path, 'w') as f:
    f.write(content)
print("Entrypoint fixed.")
