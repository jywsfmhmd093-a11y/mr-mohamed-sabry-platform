import os
for root, dirs, files in os.walk('.'):
    if 'venv' in root: continue
    for file in files:
        if file.endswith(('.py', '.html', '.css', '.js')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '' in content:
                        print('Found in', filepath)
            except Exception as e:
                pass
