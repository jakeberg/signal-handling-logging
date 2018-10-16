#!/usr/bin/env python2
"""
Signal Handling and Logging:

For this assessment you will create your own small
long-running program named `dirwatcher.py`.
This will give you experience in structuring a
long-running program, which will help you with
KenzieBot later on. The dirwatcher.py program should
accept some command line arguments that will instruct
it to monitor a given directory for text files that
are created within the monitored directory.

Your dirwatcher.py program will continually search within
all files in the directory for a 'magic' string which can
be anything you define.  This can be implemented with a
timed polling loop.  If the magic string is found, your
program should log a message indicating which file and
line number the magic text was found.  Once a magic text
occurrence has been logged, it should not be logged again unless
 it appears in the file as another subsequent line entry later on.

Files in the monitored directory may be added or deleted or appended
at any time by other processes.  Your program should log a message
when new files appear or other files disappear.

Your program should terminate itself by catching SIGTERM or SIGINT
(be sure to log a termination message).  The OS will send a signal
event to processes that it wants to terminate from the outside.
Think about when a sys admin wants to shutdown the entire computer
for maintenance with a `sudo shutdown` command.  If your process has
open file handles, or is writing to disk, or is managing other
resources, this is the OS way of telling your program that you
need to cleanup, finish any writes in progress, and release
resources before shutting down.

NOTE that handling OS signals and polling the directory that is being
watched are two separate functions of your program.  You won't be
getting an OS signal when files are created or deleted.
"""
import sys
import os
import logging
import signal
import time
import argparse
import re
from datetime import datetime, timedelta
exit_flag = False
start_time = datetime.now()

# Builds custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(filename)s : %(asctime)s : %(levelname)s : %(message)s'
    )
file_handler = logging.FileHandler('dirwatcher-log.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# Awaits signals to be recieved by signal
def signal_handler(sig_num, frame):
    """
    This is a handler for SIGTERM and SIGINT. Other signals
    can be mapped here as well (SIGHUP?)
    Basically it just sets a global flag, and main() will exit
    it's loop if the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """

    global exit_flag
    if sig_num == signal.SIGINT:
        logger.warning(
            " SIGINT recieved from the os: program terminated w/ ctr-c"
            )
        exit_flag = True
    elif sig_num == signal.SIGTERM:
        logger.warning(" SIGTERM recieved from the os: program terminated")
        exit_flag = True


def find_magic_words(d):
    """Finds all magic words and sends back an list of
    tuples containing: the word, line it was found, and the file """

    files = os.listdir(d)
    found_words = []
    for file in files:
        with open(d + "/" + file) as f:
            content = f.readlines()
            for index, line in enumerate(content):
                match = re.findall(r"magic", line)
                if match:
                    found_words.append(tuple((match[0], index, file)))
    return found_words


def log_magic_words(d, before):
    """Prints all the magic words to the log"""

    after = [w for w in find_magic_words(d)]
    added = [w for w in after if w not in before]
    removed = [w for w in before if w not in after]

    for word_added in added:
        print word_added
        logger.info(''' Magic word "{}" found at line {} in file {}'''
                    .format(word_added[0], word_added[1], word_added[2]))

    for word_added in removed:
        print word_added
        logger.info(''' Magic word "{}" is no longer at line {} in file {}'''
                    .format(word_added[0], word_added[1], word_added[2]))


def log_files(d, before):
    """Logs if a file was added or removed"""

    after = [f for f in os.listdir(d)]
    added = [f for f in after if f not in before]
    removed = [f for f in before if f not in after]

    for file_added in added:
        logger.info(''' File added {}'''
                    .format(file_added))

    for file_removed in removed:
        logger.info(''' File removed {}'''
                    .format(file_removed))


# Creates parser
def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('dir',
                        help='Initializes the directory')
    return parser


def main(args):

    # Create parser
    parser = create_parser()

    # Exit if there are no arguments
    if not args:
        parser.print_usage()
        sys.exit(1)

    # Parse args
    parsed_args = parser.parse_args(args)

    # Hook these two signals from the OS ..
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Exception handling for missing directory
    try:
        os.listdir(parsed_args.dir)
    except Exception as e:
        logger.error('''Error : {}  '''.format(e))
        sys.exit(1)

    # Interval for while loop
    some_interval = 2

    # Get server start time
    start_time = datetime.now()
    logger.info(''' Program started at : {} '''
                .format(start_time))

    # Gets lists of all found files and magic words for global variable
    files_before = [f for f in os.listdir(parsed_args.dir)]
    words_before = find_magic_words(parsed_args.dir)

    # Prints out initial message of all found files
    # and magic words when program runs
    logger.info(''' Program initialized the these files : {} '''
                .format(files_before))
    logger.info(''' Program initialized the these found magic words : {} '''
                .format(words_before))

    # Program runs while there is no exit flag at an interval specified above
    while not exit_flag:
        time.sleep(some_interval)

        # Logs words and files if they are different from last interval
        log_magic_words(parsed_args.dir, words_before)
        log_files(parsed_args.dir, files_before)

        # Gets new lists of files and words
        words_after = find_magic_words(parsed_args.dir)
        files_after = [f for f in os.listdir(parsed_args.dir)]

        # Sets global variables to new lists to check against
        words_before = words_after
        files_before = files_after

    # Logs uptime after while loop has been broken
    logger.info(''' Program ended at : {}  '''
                .format(datetime.now()))
    uptime = datetime.now() - start_time
    logger.info(''' Uptime : {} seconds '''
                .format(uptime.seconds))


if __name__ == '__main__':
    main(sys.argv[1:])
