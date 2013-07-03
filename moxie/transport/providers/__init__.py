class TransportRTIProvider(object):

    provides = []

    def handles(self, doc, *args):
        return False

    def invoke(self, doc, *args):
        raise NotImplementedError("You must implement the 'invoke' method")

    def __call__(self, *args, **kwargs):
        return self.invoke(*args, **kwargs)
