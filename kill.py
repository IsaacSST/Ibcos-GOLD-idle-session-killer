import telnetlib
import time
import sys

args = sys.argv
thresh = False
auto = False

for arg in args:
    if 'auto' in arg:
        auto = True
        interval = int(arg[5:])

    if 'th' in arg:
        thresh = True
        time_thresh = int(arg[3:])

loop = True
while loop:
    # connection
    HOST = '' #write host ip here
    USER = 'root' #write login name here
    PASS = '' #write password here
    tn = telnetlib.Telnet(HOST, 23)
    print("connected")

    # login
    tn.read_until(b'login: ')
    tn.write((USER + '\n').encode('ascii'))
    print("written login")

    tn.read_until(b'assword: ')
    tn.write((PASS + '\n').encode('ascii'))
    print("written password")

    # setting terminal type
    tn.read_until(b'erminal type? ')
    tn.write(b'vt100\n')
    print("terminal type written")

    # w command
    tn.read_until(b'# ')
    tn.write(b'w\n')
    print("w command gone through")
    time.sleep(1)

    # reading sessions into string
    out = tn.read_until(b':~').decode()
    sessions = out.split('\r\n')[3:-1]
    sessions = list(map(lambda x: x.split(), sessions))

    hitlist = []
    week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # finding sessions to kill
    for session in sessions:
        if ('m' in session[3]) and (session[7] == 'dbr'):
            hitlist.append(session[1])
        elif any(day in session[2] for day in week) and (session[1] != 'console'):
            hitlist.append(session[1])
        elif thresh:
            if ('s' not in session[3]) and (session[7] == 'dbr'):
                minute = int(session[3].split(':')[0])
                if minute >= time_thresh:
                    hitlist.append(session[1])

    print('hit list compiled')

    # getting pids and killing
    if len(hitlist) > 0:
        for hit in hitlist:
            get_pid_command = 'ps -t ' + hit + '\n'
            tn.read_until(b'# ')
            tn.write(get_pid_command.encode('ascii'))
            out = tn.read_until(b':~').decode()
            pid = out.split('\n')[2].split()[0]

            tn.read_until(b'# ')
            kill_command = 'kill -9 ' + pid + '\n'
            tn.write(kill_command.encode('ascii'))
            print(hit + ' killed')

    else:
        print('No eligible sessions')

    # terminating session
    tn.read_until(b'# ')
    tn.write(b'exit\n')
    tn.close()

    print('Disconnected\n')

    if auto:
        print('sleeping\n')
        time.sleep(interval*60)

    else:
        loop = False






