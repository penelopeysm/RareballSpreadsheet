"""
NB: To use this script you will need access to my PostgreSQL database
containing Pokemon data.
"""

import re
import os
from pathlib import Path

import psycopg

DEX_NO_NAMES = {}
CONN_STRING = os.environ.get('FLY_PG_PROXY_CONN_STRING')
with psycopg.connect(CONN_STRING) as conn:
    with conn.cursor() as cur:
        # Query the database and obtain data as Python objects.
        cur.execute(f"SELECT DISTINCT (ndex) ndex, name FROM pokemon")
        names = cur.fetchall()
        for (ndex, name) in names:
            if ndex == 669:
                DEX_NO_NAMES[669] = 'flabebe'
            elif ndex == 29:
                DEX_NO_NAMES[29] = 'nidoran-female'
            elif ndex == 32:
                DEX_NO_NAMES[32] = 'nidoran-male'
            else:
                # standardise names
                name = '-'.join(name.split()).lower()
                name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
                DEX_NO_NAMES[ndex] = name

with open('mappings1.csv', 'r') as csv:
    lines = csv.readlines()
    names, img_fnames = zip(*[line.strip().split(',', maxsplit=1) for line in lines])

    # assert that images exists
    for img in img_fnames:
        assert Path(img).exists(), f"File {img} does not exist"

    # Extract the dex number and other stuff
    rgx = re.compile(r'Gen\d/poke_(?:(?:icon)|(?:capture))_((\d+)_\d+_\w+)_n_\d+_f_([nr]).png')
    matches = []
    identifiers = []
    dex_nos = []
    shinies = []
    for img in img_fnames:
        m = rgx.fullmatch(img)
        if m:
            matches.append(m)
            identifiers.append(m.group(1))
            dex_nos.append(int(m.group(2)))
            shinies.append(m.group(3) == "r")
        else:
            raise ValueError(f"Unexpected filename not matching regex: {img}")

    # make output directories
    Path("original").mkdir(exist_ok=True)
    Path("shiny").mkdir(exist_ok=True)

    with open('mappings2.csv', 'w') as csv2:
        # Loop over images renaming them
        for name, img, identifier, dex_no in zip(names, img_fnames, identifiers, dex_nos):
            # get name corresponding to dex no (from postgres DB)
            dex_no_name = DEX_NO_NAMES[dex_no]

            # check if there are multiple images for this dex number
            if len([d for d in dex_nos if d == dex_no]) > 1:
                # get the form name
                splits = name.split(maxsplit=1)
                if len(splits) == 1:
                    output_fname = f"{dex_no_name}.png"   # basic form
                else:
                    # check for regional forms because these are written as Alolan X
                    regionals = ['Alolan', 'Galarian', 'Paldean', 'Hisuian']
                    if splits[0] in regionals:
                        form = splits[0].lower()
                        # check for extra forms
                        all_splits = name.split()
                        if len(all_splits) > 2:
                            if all_splits[-1] == '♀':
                                form = form + '_female'
                            elif all_splits[-1] == '♂':
                                form = form + '_male'
                            elif all_splits[-1].lower() == 'mime':
                                pass
                            else:
                                form = form + '_' + all_splits[-1].lower()
                    else:
                        # determine form by stripping off the species name, which
                        # is assumed to be the first word (or the first two
                        # words)
                        form = name.split(' ', maxsplit=1)[-1].strip().lower()
                        form = "_".join(form.split())
                        if form == '♀':
                            form = 'female'
                        elif form == '♂':
                            form = 'male'
                        elif form == '!':
                            form = 'exclamation'
                        elif form == '?':
                            form = 'question'
                    # remove special characters
                    form = re.sub(r'[^a-zA-Z0-9_]', '', form)
                    output_fname = f"{dex_no_name}_{form}.png"
            else:
                output_fname = f"{dex_no_name}.png"

            # rename file
            Path(img).rename(f"original/{output_fname}")

            # rename shiny (but note, some shinies don't exist)
            shiny_fname = img.replace("_n.png", "_r.png")
            if Path(shiny_fname).exists():
                Path(shiny_fname).rename(f"shiny/{output_fname}")

            # print the new mappings
            print(f"{name},{img},{output_fname}", file=csv2)
