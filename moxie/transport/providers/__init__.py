class TransportRTIProvider(object):

    provides = []

    def handles(self, doc):
        return False

    def invoke(self, doc):
        raise NotImplementedError("You must implement the 'invoke' method")

    def __call__(self, *args, **kwargs):
        return self.invoke(*args, **kwargs)
