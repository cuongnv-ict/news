#ifndef STATE_H
#define STATE_H

#include <set>

#include "utils.h"
#include "corpus.h"

using namespace std;

struct WordInfo {
public:
  int word_;
  int count_;
  int topic_assignment_;
};

class DocState {
public:
  int doc_id_;
  WordInfo* words_;
  int doc_length_;
public:
  DocState();
  ~DocState();
public:
 void setup_state_from_doc(const Document* doc); 
};

class LDAState {
public:
  LDAState();
  ~LDAState();
  void init_lda_state(double eta, double alpha, int num_topics_, int size_vocab);
  void copy_lda_state(const LDAState& src_state);
  void save_lda_state(const char* name);
  void load_lda_state(const char* name);
public:
  vector<int* > topic_lambda_; // Not counting the prior, eta
  vct_int word_counts_by_topic_;

  // Hyper parameters
  double alpha_; 
  double eta_;

  int num_topics_;
  int size_vocab_;
};

class LDA {
public: // Not fixed.
  int num_docs_;
  DocState** doc_states_;
  
  vector<int*> word_counts_by_topic_doc_;  // Number of words by topic, doc

  LDAState* lda_state_;

  // For fast Gibbs sampling using Mimno's trick.
  vector<set<int> > unique_topic_by_word_;
  vector<set<int> > unique_topic_by_doc_;
  vct smoothing_prob_;
  double smoothing_prob_sum_;
  vector<double* > doc_prob_;
  vct doc_prob_sum_;

public:
  LDA();
  ~LDA();
  
  void init_lda(double eta, double gamma, double alpha, int size_vocab);
  void setup_doc_states(const vector<Document* >& docs);
  void setup_unique_topic_by_word_(); // used at test time
  void remove_doc_states();

  int iterate_gibbs_state(bool remove, bool permute);
  int  sample_word_assignment(DocState* doc_state, int i, bool remove, vct* p);
  void doc_state_update(DocState* doc_state, int i, int update);

  double log_likelihood(const LDAState* old_lda_state = NULL);
  void save_state(const char* name);
  void load_state(const char* name);

  void init_fast_gibbs_sampling_variables();
  void save_doc_states(const char* name); 
};

#endif // STATE_H
