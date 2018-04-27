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
    'seed': 10
}

SHINGLE_CONFIG = {
    'k': 1
}

TIME_TO_DELETE = 2