import re

# Read the file
with open('d:\\Hunger Games Simulator\\main.py', 'r') as f:
    content = f.read()

# Find the first return result and remove everything after it until the final part
parts = content.split('return result', 2)
if len(parts) >= 3:
    before_first_return = parts[0] + 'return result'
    
    # Find the final result handling part
    final_part_start = parts[2].find('# Write final result to web output file')
    if final_part_start != -1:
        final_part = parts[2][final_part_start:]
        new_content = before_first_return + '\n\n' + final_part
    else:
        new_content = before_first_return + '\n\nif __name__ == "__main__":\n    main()'
    
    with open('d:\\Hunger Games Simulator\\main.py', 'w') as f:
        f.write(new_content)
    
    print('File cleaned successfully')
else:
    print('Could not find the return statements')