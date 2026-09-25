import os
BASE = r'D:\PROJECTS\trademind\backend'
def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  {path}')

write('app/features/returns.py', open(os.path.join(BASE, 'app/features/returns.py')).read() if os.path.exists(os.path.join(BASE, 'app/features/returns.py')) else '')
print('Test')