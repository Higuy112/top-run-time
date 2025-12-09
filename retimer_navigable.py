import csv
from pathlib import Path
import easygui
import datetime

def showCommands():
    print("Commands:")
    print(" n/next        - go to next pause")
    print(" p/prev/back   - go to previous pause")
    print(" scp           - mark current pause as 'scp' (settings change pause)")
    print(" dlp           - mark current pause as 'dlp' (dimension load pause)")
    print(" tdlp          - mark current pause as 'tdlp' (timed dimension load pause)")
    print(" np            - mark current pause as 'np' (normal pause)")
    print(" up            - mark current pause as 'up' (untimed pause)")
    print(" auto          - reset current pause to automatic detection (if available)")
    print(" jump <num>    - go to pause index number")
    print(" list          - show all pauses and assigned types")
    print(" finish/save   - finish editing and write output")
    print(" quit          - exit without saving")
    
showCommands()
print('\n')
print('this tool is designed to work with version 8+ any% logs')
print('if the timer version is 7.2.4 or lower, or uses a different timer category, user the other retimer')
print('\n\n')

def spaces(n):
    s = ''
    while n<9:
        s += ' '
        n += 1
    return s

def converttosecs(time):
    '''takes time in mm:ss:xxx and converts to seconds'''
    mins = int(time[0:2])
    secs = int(time[3:5])
    ms = int(time[6:9]) / 1000

    time = mins*60 + secs + ms
    return time

# ...existing code...
def parse_pause(line):
    """Parse a CSV line into a dict. Does not prompt; sets auto type when detectable."""
    parts = line[0].split()
    pnum = str(parts[0])
    igt = parts[1]
    startrta = parts[2]
    endrta = parts[3]
    plength = float(parts[4])
    ptype_tokens = line[-2].split()

    # auto-detect
    if ptype_tokens and ptype_tokens[-1] == 'player':
        auto = None  # needs manual
    elif ptype_tokens and (ptype_tokens[-1] == 'dimension' or ptype_tokens[-1] == 'load?' or ptype_tokens[-1] == 'ticks'):
        auto = 'dl'
    elif ptype_tokens and ptype_tokens[-1] == 'world':
        auto = 'rl'
    else:
        auto = None

    return {
        'pnum': pnum,
        'igt_str': igt,
        'start_rta': startrta,
        'end_rta': endrta,
        'plength': plength,
        'auto': auto,
        'assigned': None,  # user-specified
        'line': line,
    }

fdir = easygui.diropenbox()
fpath = f'{fdir}\\speedrunigt\\logs\\igt_timer.log'
with open(fpath, newline='') as f:
    r = csv.reader(f)
    file = list(r)
with open(fpath, newline='') as f:
    lines = f.readlines()
    origfile = [line.rstrip() for line in lines]

responses = []
newf = ['type     start RTA      end RTA        length         time added\n']

file = file[1:]

igt = file[-5][0].split()
igt = converttosecs(igt[-1])
print('starting igt =', igt, 'seconds')
print()

# build pauses list
pauses = [parse_pause(line) for line in file[:-6]]

def show_pause(p):
    assigned = p['assigned'] if p['assigned'] else (p['auto'] if p['auto'] else 'UNSET')
    print(f"pause {p['pnum']}: {p['start_rta']} -> {p['end_rta']} at {p['igt_str']} IGT, length={p['plength']}, type={assigned}")

def list_assignments():
    for i, p in enumerate(pauses, start=1):
        assigned = p['assigned'] if p['assigned'] else (p['auto'] if p['auto'] else 'UNSET')
        print(f"{i:3}: {p['pnum']:3} | {p['start_rta']} - {p['end_rta']} | len={p['plength']:5.3f} | {assigned}")

# navigable loop
idx = 0
n = len(pauses)
print("Interactive navigation: 'h' for help.")

while True:
    print("-" * 60)
    show_pause(pauses[idx])
    cmd = input("enter type of pause (h for help): ").strip().lower()
    if not cmd:
        continue
    parts = cmd.split()
    c = parts[0]

    if c in ('h', 'help'):
        showCommands()
    elif c in ('n', 'next'):
        if idx < n-1:
            idx += 1
        else:
            print("Already at last pause.")
    elif c in ('p', 'prev'):
        if idx > 0:
            idx -= 1
        else:
            print("Already at first pause.")
    elif c in ('scp', 'dlp', 'tdlp', 'np', 'up'):
        pauses[idx]['assigned'] = c
        print(f"Set pause {pauses[idx]['pnum']} to {c}")
        if idx < n-1:
            idx += 1
            while idx < n:
                if pauses[idx]['auto'] == 'dl':
                    print("Next pause is a dimension load; skipping.")
                    idx += 1
                elif pauses[idx]['auto'] == 'rl':
                    print("Next pause is a world load; manually retime, skipping.")
                    idx += 1
                else:
                    break
        else:
            print("Last pause reached. To finish, use 'finish' command.")
    elif c == 'auto':
        pauses[idx]['assigned'] = None
        print("Reset to auto (if available).")
    elif c == 'jump':
        if len(parts) < 2 or not parts[1].isdigit():
            print("Usage: jump <index>")
            continue
        j = int(parts[1]) - 1
        if 0 <= j < n:
            idx = j
        else:
            print("Index out of range.")
    elif c == 'list':
        list_assignments()
    elif c in ('finish', 'save'):
        print("Finishing and saving...")
        break
    elif c == 'quit':
        print("Exiting without saving.")
        exit(0)
    else:
        print("Unknown command. 'h' for help.")

# apply assignments and compute final IGT
nline = 1
for p in pauses:
    print('pause', nline, ':')
    plength = p['plength']
    ptype = p['assigned'] if p['assigned'] else p['auto']
    # if still None, 'np' by default
    if ptype is None:
        print(f"Pause {p['pnum']} left UNSET. Defaulting to 'np'.")
        ptype = 'np'
    # build newl string similar to original
    newl = ptype+spaces(len(ptype))+p['start_rta']+'      '+p['end_rta']+'      '+"%.3f" % plength+'          '

    if ptype == 'scp':
        if plength > 5:
            igt += plength - 5
            print('everything after first 5s of this scp added back in =', plength-5)
            newl += str(plength - 5)
        else:
            print('no time added back for this scp of length =', plength)
            newl += '0'
    elif ptype == 'dlp':
        print('no time added back in for this dlp of length =', plength)
        origfile[nline] += ' - dimension load pause, untimed'
        newl += '0'
    elif ptype == 'tdlp':
        igt += plength
        print('length of this tdlp added back in =', plength)
        newl += str(plength)
    elif ptype == 'np':
        igt += plength
        print('length of this np added back in =', plength)
        newl += str(plength)
    elif ptype == 'up':
        print('no time added back for this up of length =', plength)
        origfile[nline] += ' - untimed pause'
        newl += '0'
    elif ptype == 'dl':
        print('no time added back for this dimension load of length =', plength)
        newl += '0'
    elif ptype == 'rl':
        print('no time added back for this reload of length =', plength, '(manual retime required)')
        newl += '0'
    if ptype == 'back':
        nline -= 1
    else:
        newf.append(newl)
        nline += 1
print()

igt = round(igt, 3)
print('final igt =', igt, 'seconds')
ftime = (str(datetime.timedelta(seconds=igt)))[:-3]
print(ftime)

newf.append('')
newf.append(origfile[-5])
newf.append('retimed IGT for top run retiming to '+ftime)
#print(newf)
fname = input('enter name for output file: ')+'.txt'
#will go in same folder as SavesFolderReader
outfile = Path(fdir).parent/fname
with open(outfile, 'w') as f:
    for line in newf:
        f.write(line+'\n')

input('press enter to exit...')
