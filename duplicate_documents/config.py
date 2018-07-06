import datetime


LSH_CONFIG = {
    'num_permutation': 150,
    'b': 30,
    'r': 5,
    'storage':{
        'type': 'redis',
        'redis': {'host': 'localhost', 'port': 6379}
   },
    'similarity_threshold': 0.7
}

MINHASH_CONFIG = {
    'num_permutation': 150,
    'seed': datetime.datetime.now().microsecond
}

SHINGLE_CONFIG = {
    'k': 1
}


TIME_TO_DELETE = 7 # time by day