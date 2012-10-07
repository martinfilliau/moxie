class Provider(object):

    def handles(self, doc):
        return False

    def invoke(self, doc):
        raise NotImplementedError("You must implement the 'invoke' method")
