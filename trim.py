import os

for directory in ['original', 'shiny']:
    for fname in os.listdir(directory):
        if fname.endswith('png'):
            print(f'Processing {directory}/{fname}')
            os.system(f'convert {directory}/{fname} -trim +repage {directory}/{fname}')
            os.system(f'convert {directory}/{fname} -bordercolor transparent -border 3 {directory}/{fname}')
