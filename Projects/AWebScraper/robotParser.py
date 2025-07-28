class RobotParser:
    def __init__(self, robot_txt: str):
        self.rbt_txt = robot_txt
        self.rules = { "disallow": [], "allow": [] }

    def parse(self):
        capture = False
        for line in self.rbt_txt.splitlines():
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            if ':' not in line:
                continue
            
            tag, value = map(str.strip, line.split(":", 1))
            tag = tag.lower()

            if tag == "user-agent":
                if value == "*":
                    capture = value == "*"
            
            elif capture and tag in ["disallow", "allow"]:
                self.rules[tag].append(value)
        
        return self.rules






