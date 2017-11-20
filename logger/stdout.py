import sys


class WriteOut_(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'a')

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        sys.stdout = self

    def stop(self):
        self.log.close()
        sys.stdout = self.terminal

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass


def stdout_to(filename):
    return WriteOut_(filename)
