import sys, os
import numpy as np
from io import open
import utils

import matplotlib
# check display and when ssh to server using command:
# ssh -X "your_login"
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    matplotlib.use('Agg')

import matplotlib.pyplot as plt; plt.rcdefaults()
import matplotlib.pyplot as plt



# resize name of x-bar
matplotlib.rcParams.update({'xtick.labelsize' : 6})

TOPIC_PROBABILITY_THRESHOLD = 0.5
TOPIC_MERGE_PROBABILITY_THRESHOLD = 0.35
TOP_DOCUMENTS = 5
TOPIC_MERGE_THRESHOLD = 0.5
MINIMUM_DOCS = 6

# print topics to file
def print_topics(beta_file, topics_title, vocab_file, nwords, result_file):
    min_float = -sys.float_info.max
    vocab = file(vocab_file, 'r').readlines()
    vocab = map(lambda x: x.strip(), vocab)
    with open(result_file, 'w', encoding='utf-8') as fp:
        for topic_no, topic in enumerate(file(beta_file, 'r')):
            fp.write(u'topic %03d - %s\n' % (topic_no, topics_title[topic_no]))
            topic = np.array(topic.split(), dtype = float)
            for i in range(nwords):
                index = topic.argmax()
                fp.write(unicode('   %s \t\t %f\n' % (vocab[index], topic[index]), encoding='utf-8'))
                topic[index] = min_float
            fp.write(u'\n')


def get_topics_title(doc_states, titles_file):
    theta = []; topics_title = []
    # normalize doc states
    with open(doc_states, 'r') as fp:
        for state in fp:
            state = map(float, state.strip('\n').split())
            total = sum(state)
            st = map(lambda x: x/total, state)
            theta.append(st)
    theta = np.array(theta) # theta[D][K]
    # get topic name
    with open(titles_file, 'r', encoding='utf-8') as fp:
        titles = fp.read().split(u'\n')
        for k in xrange(theta.shape[1]):
            try:
                rate = theta[:, k] # get data column i-th
                doc_id = np.argmax(rate)
                topics_title.append(titles[doc_id])
            except:
                topics_title.append(u'')
                continue
    return theta, topics_title, titles


def get_trending_topics(theta, topic_titles, titles, domain):
    ntopics = theta.shape[1]
    count_topics = np.zeros((ntopics), dtype=np.int)
    docs_topic = {k : [] for k in xrange(ntopics)}
    docs_id = {k : [] for k in xrange(ntopics)}
    topics_dup = {k:set() for k in xrange(ntopics)}
    for i, d in enumerate(theta): # i : index and d : topic propotion of doc
        k = np.argmax(d)
        if d[k] < TOPIC_PROBABILITY_THRESHOLD:
            continue
        for j in xrange(ntopics):
            if d[j] > TOPIC_MERGE_PROBABILITY_THRESHOLD:
                topics_dup[j].update([i])
        count_topics[k] += 1
        docs_topic[k].append(d[k])
        docs_id[k].append(i)
    merge_topics(topics_dup, count_topics, docs_topic, docs_id, topic_titles=topic_titles)
    total = sum(count_topics)
    if total == 0:
        return {}, {}
    topics_propotion = map(lambda x: float(x) / float(total), count_topics)
    trending = np.argsort(topics_propotion)[::-1]
    trending_threshold = get_trending_threshold(ntopics)
    trending = filter(lambda x: topics_propotion[x] * ntopics > trending_threshold
                                and count_topics[x] >= MINIMUM_DOCS, trending)
    trending_titles = {i : topic_titles[i] for i in trending}
    docs_trending = get_docs_trending(docs_id, docs_topic, trending_titles, titles)
    # draw_document_distribution(trending_titles, topics_propotion, total, domain)
    return trending_titles, docs_trending


def get_trending_threshold(ntopics):
    if ntopics >= 100:
        return 2.75
    elif ntopics >= 75:
        return 2.625
    elif ntopics >= 50:
        return 2.5
    elif ntopics >= 30:
        return 2.4
    elif ntopics >= 20:
        return 2.25
    else: return 2.1


def merge_topics(topics_dup, count_topics, docs_topic, docs_id, topic_titles=None):
    step_one = merge_step_one(topics_dup)
    step_two = merge_step_two(step_one)
    if topic_titles != None:
        merge_print(step_two, topic_titles)
    final = merge_sort(step_two, docs_topic)
    merge_update_topics(final, count_topics, docs_topic, docs_id)


def merge_step_one(topics_dup):
    step_one = []
    for k1, s1 in topics_dup.items():
        for k2, s2 in topics_dup.items():
            if k1 >= k2: continue
            similarity = get_similarity_score(s1, s2)
            if similarity > TOPIC_MERGE_THRESHOLD:
                exist = False
                for i in xrange(len(step_one)):
                    if k1 in step_one[i] or k2 in step_one[i]:
                        exist = True
                        step_one[i].update([k1, k2])
                if not exist:
                    step_one.append(set([k1, k2]))
    return step_one


def merge_step_two(step_one):
    step_two = []
    for i in xrange(len(step_one)):
        m = step_one[i]
        if len(m) == 0: continue
        for j in xrange(len(step_one)):
            if i >= j or len(step_one[j]) == 0: continue
            if len(m.intersection(step_one[j])) > 0:
                m = m.union(step_one[j])
                step_one[j] = set([])
        step_two.append(tuple(m))
    return step_two


def merge_sort(step_two, docs_topic):
    final = {}
    for m in step_two:
        maximum = m[0]
        for mm in m:
            if len(docs_topic[mm]) > len(docs_topic[maximum]):
                maximum = mm
        final.update({maximum: filter(lambda x: x != maximum, m)})
    return final


def merge_update_topics(merge_final, count_topics, docs_topic, docs_id):
    for k, s in merge_final.items():
        if len(s) == 0 : continue
        for kk in s:
            if count_topics[kk] == 0: continue
            count_topics[k] += count_topics[kk]
            count_topics[kk] = 0
            docs_topic[k] += docs_topic[kk]
            docs_topic[kk] = []
            docs_id[k] += docs_id[kk]
            docs_id[kk] = 0


def merge_print(merge, topic_titles):
    for m in merge:
        print('merge group:')
        for mm in m:
            print('topic %d - %s' % (mm, topic_titles[mm]))
        print('**************************')


def get_docs_trending(docs_id, docs_topic, trending_titles, titles):
    docs_trending = {}
    for k in trending_titles.keys():
        if len(docs_topic[k]) == 0:
            continue
        doc_topic = np.argsort(docs_topic[k])[::-1]
        doc_id = docs_id[k]
        for i in doc_topic:
            try:
                d = doc_id[i]
                docs_trending[k].update([titles[d]])
            except:
                docs_trending.update({k : set([titles[d]])})
        docs_trending[k] = list(docs_trending[k])
        # docs_trending[k] = docs_trending[k][:TOP_DOCUMENTS]
    return docs_trending


def draw_document_distribution(trending_topics, count_topics, total, domain):
    domain_nor = domain.replace(u' ', u'-').lower()
    output_dir = os.path.join(u'static', domain_nor)
    utils.delete_dir(output_dir)
    utils.mkdir(output_dir)
    objects = []
    for k in xrange(len(count_topics)):
        try:
            if len(count_topics) >= 50:
                _ = trending_topics[k]
            objects.append(unicode(k))
        except:
            objects.append(u'')
    performance = map(lambda x: x * 100, count_topics)
    y_pos = np.arange(len(objects))
    plt.bar(y_pos, performance, align='center', alpha=0.5)
    plt.xticks(y_pos, objects)
    plt.ylabel('percent')
    plt.title('Document distribution by topics - num_docs = %d' % (total))
    # plt.show()
    plt.tight_layout(pad=0.4, w_pad=1.4, h_pad=1.0)

    plt.savefig(os.path.join(output_dir, 'documents_distribution.png'), dpi=100)


def get_similarity_score(set1, set2):
    if len(set1) >= len(set2):
        m = float(len(set2))
    else: m = float(len(set1))
    intersection = float(len(set1.intersection(set2)))
    return intersection / m
