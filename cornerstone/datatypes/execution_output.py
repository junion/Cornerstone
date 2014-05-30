

class ExecutionOutputEvent(object):
    def __init__(self, asr_config):
        self.asr_config = asr_config

    def __str__(self):
        return self.asr_config 


