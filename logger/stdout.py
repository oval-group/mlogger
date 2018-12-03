import sys


class WriteOut_(object):
    def __init__(self, filename, enabled=True):
        self.terminal = sys.stdout
        self.enabled = enabled
        if self.enabled:
            self.log = open(filename, 'a')

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        if self.enabled:
            sys.stdout = self

    def stop(self):
        sys.stdout = self.terminal
        if self.enabled:
            self.log.close()

    def write(self, message):
        self.terminal.write(message)
        if self.enabled:
            self.log.write(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass


def stdout_to(filename, enabled=True):
    return WriteOut_(filename, enabled)
