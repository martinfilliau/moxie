class AbstractSearch(object):

    def __init__(self, index):
        """
        @param index name of the index / collection / core
        """
        pass

    def index(self, document):
        pass

    def search(self, query):
        pass

    def get_by_ids(self, document_ids):
        """
        Get documents by their unique ID
        """
        pass