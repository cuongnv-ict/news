import cPickle as pickle
def pickle_save(object, path):
    pickle.dump(object, open("%s" % (path), "wb"))
def pickle_load(path):
    return pickle.load(open("%s" % path, "rb"))