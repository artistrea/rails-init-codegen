STATES = {
    "UNSCOPED": 0,
    "TABLESCOPE": 1,
}

class FileParser:
    def build(self):
        self.cur_state = STATES["UNSCOPED"]
        self.schema = {}

    def read_line(self, line):
        line = line.strip()
        print(line)