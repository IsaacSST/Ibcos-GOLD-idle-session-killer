######################################################################################
# python 3 script for killing user sessions of Ibcos gold classic
# author: Isaac Thompson 20/03/2021 - 26/05/2021, Lloyd Ltd

######################################################################################
import telnetlib
import time
import sys
import math as m
from getpass import getpass

#getting arguments from command line
args = sys.argv
#setting defaults
thresh = False
auto = False
exclude = False
max_sessions = 120
dynamic_thresh = False
host = 'localhost'

#reading arguments into variables
for arg in args:
    if '-host' in arg:
        host = arg[6:]

    if '-auto' in arg:
        auto = True
        interval = int(arg[6:])

    if '-th' in arg:
        thresh = True
        time_thresh = int(arg[4:])

    if '-x' in arg:
        exclude = True
        exclude_str = arg[3:]

    if '-max' in arg:
        max_sessions = int(arg[5:])
        dynamic_thresh = True

#getting login details
username = input("Username: ")
password = getpass()

loop = True
while loop:
    # connection
    HOST = host
    PORT = 23
    #getting port if port is specified in IP
    if ':' in HOST:
        PORT = int(HOST.split(':')[1])
        HOST = HOST.split(':')[0]

    USER = username
    PASS = password

    #attempting to connect to server
    connected = False
    while not connected:
        try:
            tn = telnetlib.Telnet(HOST, PORT)
            print("connected")
            connected = True
        except:
            print('unable to connect to host')
            print('retrying...')
            time.sleep(2)


    # login
    try:
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
    except:
        print('Unable to execute login sequence')
        print('Retrying...')
        tn.read_all()
        tn.close()
        time.sleep(2)
        next

    #setting dynamic threshold if max sessions specified
    if dynamic_thresh:
        tn.read_until(b'# ')
        tn.write(b"show | grep 'Users = ' | cat\n")
        out = tn.read_until(b':~').decode()
        users = int(out.split('\r\n')[1].split('Users = ')[1].split()[0])
        factor = (m.exp(max(0.0, (users - 0.8*0.96*max_sessions) / (0.2*0.96*max_sessions))) - 1) / (m.e - 1)
        time_thresh = 60 - int(factor*20.0)
        thresh = True
        print(str(users) + ' of ' + str(max_sessions) + ', setting threshold: ' + str(time_thresh) + ' mins')


    # w command
    try:
        tn.read_until(b'# ')
        tn.write(b'w\n')
        print("w command gone through")
        time.sleep(1)
    except:
        print("w command failed")
        print('Retrying...')
        tn.read_all()
        tn.close()
        time.sleep(2)
        next

    # reading sessions into string
    out = tn.read_until(b':~').decode()
    sessions = out.split('\r\n')[3:-1]
    sessions = list(map(lambda x: x.split(), sessions))

    #initialising hitlist of sessions that will be killed
    hitlist = []

    #list of days of week - if a session has any of these in its show line then it will be killed as it means it has been logged in for more than a day, and might be a ghost session
    week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # finding sessions to kill
    for session in sessions:
        if ('m' in session[3]) and (session[7] == 'dbr'):
            hitlist.append(session[1])
        elif any(day in session[2] for day in week) and (session[1] != 'console') and (session[0] != 'root'):
            hitlist.append(session[1])
        elif thresh:
            if ('s' not in session[3]) and (session[7] == 'dbr'):
                minute = int(session[3].split(':')[0])
                if minute >= time_thresh:
                    hitlist.append(session[1])

    print('hit list compiled')

    #getting list of pids to exclude (e.g tills, specific people, DPs) if wanting to avoid killing them
    if exclude:
        ex_pids = []
        tn.read_until(b'# ')
        show_command = 'show | grep -E -i "' + exclude_str + '"\n'
        tn.write(show_command.encode('ascii'))
        out = tn.read_until(b':~').decode()
        sessions = out.split('\r\n')[1:-1]
        for s in sessions:
            pid = s.split()[-1]
            ex_pids.append(pid)


    # getting pids and killing
    if len(hitlist) > 0:
        for hit in hitlist:
            get_pid_command = 'ps -t ' + hit + '\n'
            tn.read_until(b'# ')
            tn.write(get_pid_command.encode('ascii'))
            out = tn.read_until(b':~').decode()
            try:
                pid = out.split('\n')[2].split()[0]
                if exclude:
                    if pid in ex_pids:
                        continue
                tn.read_until(b'# ')
                kill_command = 'kill -9 ' + pid + '\n'
                tn.write(kill_command.encode('ascii'))
                print(hit + ' killed')
            except:
                print("Unable to kill " + hit)

    else:
        print('No eligible sessions')

    # terminating connection
    tn.read_until(b'# ')
    tn.write(b'exit\n')
    tn.close()

    print('Disconnected\n')

    if auto:
        print('sleeping\n')
        time.sleep(interval*60)

    else:
        loop = False






