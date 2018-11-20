import datetime


LSH_CONFIG = {
    'num_permutation': 500,
    'b': 100,
    'r': 5,
    'storage':{
        'type': 'redis',
        'redis': {'host': 'localhost', 'port': 6379}
   },
    'similarity_threshold': 0.5
}

MINHASH_CONFIG = {
    'num_permutation': 500,
    'seed': datetime.datetime.now().microsecond
}

SHINGLE_CONFIG = {
    'k': 1
}


TIME_TO_DELETE = 3 # time by day