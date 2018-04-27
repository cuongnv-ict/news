#include <assert.h>
#include <algorithm>
#include "state.h"

DocState::DocState() {
  words_ = NULL;
}

DocState::~DocState() {
  if (words_ != NULL) {
    delete [] words_;
    words_ = NULL;
  }
}

void DocState::setup_state_from_doc(const Document* doc) {
  int word, count;
  doc_length_ = doc->total_;
  words_ = new WordInfo[doc_length_];
  int m = 0;
  for (int n = 0; n < doc->length_; ++n) {
    word  = doc->words_[n];
    count = doc->counts_[n];
    for (int j = 0; j < count; ++j) {
      words_[m].word_ = word;
      words_[m].count_ = 1; // If we want approximate Gibbs, we could let count_ not 1.
      words_[m].topic_assignment_ = -1;
      ++m;
    }
  }
}

LDAState::LDAState() {
}

LDAState::~LDAState() {
  vct_ptr_free(&topic_lambda_);
}

void LDAState::init_lda_state(double eta, double alpha, int num_topics, int size_vocab) {
  eta_ = eta;
  alpha_ = alpha;
  size_vocab_ = size_vocab;

  num_topics_ = num_topics;
  vct_ptr_resize(&topic_lambda_, num_topics_, size_vocab_); 
  word_counts_by_topic_.resize(num_topics_, 0);
}

void LDAState::copy_lda_state(const LDAState& src_state) {
  eta_ = src_state.eta_;
  alpha_ = src_state.alpha_;
  size_vocab_ = src_state.size_vocab_;

  num_topics_ = src_state.num_topics_;
  
  if (topic_lambda_.size() < src_state.topic_lambda_.size()) {
    vct_ptr_resize(&topic_lambda_, src_state.topic_lambda_.size(), size_vocab_); 
  }
  for (int i = 0; i < num_topics_; ++i) {
    memcpy(topic_lambda_[i], src_state.topic_lambda_[i], size_vocab_ * sizeof(int));
  }

  word_counts_by_topic_ = src_state.word_counts_by_topic_;
}

void LDAState::load_lda_state(const char* name) {
  char filename[500];

  sprintf(filename, "%s.info", name);
  FILE* info_file = fopen(filename, "r");
  fscanf(info_file, "eta: %lf\n", &eta_);
  fscanf(info_file, "alpha: %lf\n", &alpha_);
  fscanf(info_file, "size_vocab: %d\n", &size_vocab_);
  fscanf(info_file, "num_topics: %d\n", &num_topics_);
  fclose(info_file);

  word_counts_by_topic_.resize(num_topics_, 0.0); 
  sprintf(filename, "%s.counts", name);
  FILE* topic_count_file = fopen(filename, "r");
  for (int k = 0; k < num_topics_; ++k) {
    fscanf(topic_count_file, "%d", &word_counts_by_topic_[k]);
  }
  fclose(topic_count_file);

  vct_ptr_resize(&topic_lambda_, num_topics_, size_vocab_);
  sprintf(filename, "%s.topics", name);
  FILE* topic_file = fopen(filename, "r");
  for (int k = 0; k < num_topics_; ++k) {
    for (int w = 0; w < size_vocab_; ++w) {
      fscanf(topic_file, "%d", &topic_lambda_[k][w]);
    }
  }
  fclose(topic_file);
}

void LDAState::save_lda_state(const char* name) {
  char filename[500];

  sprintf(filename, "%s.info", name);
  FILE* info_file = fopen(filename, "w");
  fprintf(info_file, "eta: %lf\n", eta_);
  fprintf(info_file, "alpha: %lf\n", alpha_);
  fprintf(info_file, "size_vocab: %d\n", size_vocab_);
  fprintf(info_file, "num_topics: %d\n", num_topics_);
  fclose(info_file);

  sprintf(filename, "%s.counts", name);
  FILE* topic_count_file = fopen(filename, "w");
  for (int k = 0; k < num_topics_; ++k) {
    fprintf(topic_count_file, "%d\n", word_counts_by_topic_[k]);
  }
  fclose(topic_count_file);

  sprintf(filename, "%s.topics", name);
  FILE* topic_file = fopen(filename, "w");
  for (int k = 0; k < num_topics_; ++k) {
    fprintf(topic_file, "%d", topic_lambda_[k][0]);
    for (int w = 1; w < size_vocab_; ++w) {
      fprintf(topic_file, " %d", topic_lambda_[k][w]);
    }
    fprintf(topic_file, "\n");
  }
  fclose(topic_file);
}
 
LDA::LDA() {
  doc_states_ = NULL;
  lda_state_ = NULL;
}

LDA::~LDA() {
  remove_doc_states();
  if (lda_state_ != NULL) delete lda_state_;
  lda_state_ = NULL;
}

void LDA::remove_doc_states() {
  if (doc_states_ != NULL) {
    for (int d = 0; d < num_docs_; ++d) {
      DocState* doc_state = doc_states_[d];
      delete doc_state;
    }
    delete [] doc_states_;
    doc_states_ = NULL;
  }
  vct_ptr_free(&word_counts_by_topic_doc_);

  smoothing_prob_.clear();
  vct_ptr_free(&doc_prob_);
  doc_prob_sum_.clear();
  unique_topic_by_doc_.clear();
}

void LDA::init_lda(double eta, double gamma, double alpha, int size_vocab) {
  lda_state_ = new LDAState();
  lda_state_->init_lda_state(eta, gamma, alpha, size_vocab);
}

void LDA::setup_doc_states(const vector<Document* >& docs) {
  remove_doc_states();
  num_docs_ = docs.size();
  doc_states_ = new DocState* [num_docs_];
  for (int d = 0; d < num_docs_; ++d) {
    DocState* doc_state = new DocState();
    doc_state->doc_id_ = d;
    doc_state->setup_state_from_doc(docs[d]);
    doc_states_[d] = doc_state;
  }

  vct_ptr_resize(&word_counts_by_topic_doc_, lda_state_->word_counts_by_topic_.size(), num_docs_);
  init_fast_gibbs_sampling_variables();
}

void LDA::setup_unique_topic_by_word_() { 
  for (int k = 0; k < lda_state_->num_topics_; ++k)
    for(int w = 0; w < lda_state_->size_vocab_; ++w)
      if (lda_state_->topic_lambda_[k][w] > 0)  
        unique_topic_by_word_[w].insert(k);
}

int LDA::iterate_gibbs_state(bool remove, bool permute) {
  if (permute) { // Permute data.
    rshuffle(doc_states_, num_docs_, sizeof(DocState*));
    for (int j = 0; j < num_docs_; ++j)
      rshuffle(doc_states_[j]->words_, doc_states_[j]->doc_length_, sizeof(WordInfo));
  }
  vct p(lda_state_->num_topics_);
  int total_change = 0;
  for (int j = 0; j < num_docs_; ++j) {
    DocState* doc_state = doc_states_[j];
    for (int i = 0; i < doc_state->doc_length_; ++i) {
      total_change += sample_word_assignment(doc_state, i, remove, &p); 
    }
  }
  //sample_posterior_sticks();
  return total_change;
}

int LDA::sample_word_assignment(DocState* doc_state, int i, bool remove, vct* p) {
  int old_k = -1, k;
  if (remove) { 
    old_k = doc_state->words_[i].topic_assignment_;
    doc_state_update(doc_state, i, -1);
  }

  int d = doc_state->doc_id_;
  int w = doc_state->words_[i].word_;

  double p_w = 0.0;
  set<int>::iterator it = unique_topic_by_word_[w].begin(); 
  int j = 0;
  for (; it != unique_topic_by_word_[w].end(); ++it, ++j) {
    k = *it;
    p->at(j) = lda_state_->topic_lambda_[k][w] * (smoothing_prob_[k] + doc_prob_[k][d]);
    p_w += p->at(j);
    p->at(j) = p_w;
  }
  double total_p = p_w + (doc_prob_sum_[d] + smoothing_prob_sum_) * lda_state_->eta_;
  double u = runiform() * total_p;
  if (u < p_w) { // in the word region.
    it = unique_topic_by_word_[w].begin();
    for (j = 0; it != unique_topic_by_word_[w].end(); ++it, ++j) {
      if (u < p->at(j)) {
        k = *it;
        break;
      }
    }
  } else {
    u = (u - p_w) / lda_state_->eta_; 
    if (u < doc_prob_sum_[d]) { // In the doc region,
      it = unique_topic_by_doc_[d].begin();
      total_p = 0.0;
      for (; it != unique_topic_by_doc_[d].end(); ++it) {
        k = *it;
        total_p += doc_prob_[k][d];
        if (u < total_p) break;
      }
    } else { // In the smoothing region.
      u = u - doc_prob_sum_[d];
      total_p = 0.0;
      for (k = 0; k < lda_state_->num_topics_; ++k) {
        total_p += smoothing_prob_[k];
        if (u < total_p) break;
      }
    }
  }

  doc_state->words_[i].topic_assignment_ = k;
  doc_state_update(doc_state, i, 1);
  return int(old_k != k);
}

void LDA::doc_state_update(DocState* doc_state, int i, int update) {
  int d = doc_state->doc_id_;
  int w = doc_state->words_[i].word_;
  int c = doc_state->words_[i].count_; 
  int k = doc_state->words_[i].topic_assignment_;
  //assert(k >= 0); // we must have it assigned before or assigned to a new one.

  if (update > 0)  {
    if (lda_state_->topic_lambda_[k][w] == 0)
      unique_topic_by_word_[w].insert(k);
    if (word_counts_by_topic_doc_[k][d] == 0)
      unique_topic_by_doc_[d].insert(k);
  }

  update *= c;
  // Update LDA state
  smoothing_prob_sum_ -= smoothing_prob_[k];
  lda_state_->word_counts_by_topic_[k] += update;
  lda_state_->topic_lambda_[k][w] += update;

  doc_prob_sum_[d] -= doc_prob_[k][d];
  word_counts_by_topic_doc_[k][d] += update;

  if (update < 0 ) {
    if (lda_state_->topic_lambda_[k][w] == 0)
      unique_topic_by_word_[w].erase(k);
    if (word_counts_by_topic_doc_[k][d] == 0) 
      unique_topic_by_doc_[d].erase(k);
  }

  double etaW = lda_state_->size_vocab_ * lda_state_->eta_;
  smoothing_prob_[k] = lda_state_->alpha_ / (lda_state_->word_counts_by_topic_[k] + etaW);
  smoothing_prob_sum_ += smoothing_prob_[k];
  doc_prob_[k][d] = word_counts_by_topic_doc_[k][d] / (lda_state_->word_counts_by_topic_[k] + etaW);
  doc_prob_sum_[d] += doc_prob_[k][d];
}

double LDA::log_likelihood(const LDAState* old_lda_state) {
  double likelihood = 0.0;

  double alphaK = lda_state_->alpha_ * lda_state_->num_topics_;
  double lg_alpha = lgamma(lda_state_->alpha_);

  likelihood += num_docs_ * lgamma(alphaK);

  for (int i = 0; i < num_docs_; ++i) {
    int d = doc_states_[i]->doc_id_;
    likelihood -= lgamma(alphaK + doc_states_[d]->doc_length_);
    for (int k = 0; k < lda_state_->num_topics_; ++k) {
      if (word_counts_by_topic_doc_[k][d] > 0) {
        likelihood += lgamma(lda_state_->alpha_ + word_counts_by_topic_doc_[k][d]);        
        likelihood -= lg_alpha;
      }
    }
  }

  int old_num_topics = 0;
  if (old_lda_state != NULL) {
    old_num_topics = old_lda_state->num_topics_;
  }
  double etaW = lda_state_->size_vocab_ * lda_state_->eta_;
  for (int k = 0; k < old_num_topics; ++k) {
    if (lda_state_->word_counts_by_topic_[k] > old_lda_state->word_counts_by_topic_[k]) {
      likelihood += lgamma(old_lda_state->word_counts_by_topic_[k] + etaW);
      likelihood -= lgamma(lda_state_->word_counts_by_topic_[k] + etaW);
      for (int w = 0; w < lda_state_->size_vocab_; ++w) {
        if (lda_state_->topic_lambda_[k][w] > old_lda_state->topic_lambda_[k][w]) {
          likelihood -= lgamma(old_lda_state->topic_lambda_[k][w] + lda_state_->eta_);
          likelihood += lgamma(lda_state_->topic_lambda_[k][w] + lda_state_->eta_);
        }
      }
    }
  }

  double lg_eta = lgamma(lda_state_->eta_);
  double lg_etaW = lgamma(etaW);
  for (int k = old_num_topics; k < lda_state_->num_topics_; ++k) {
    if (lda_state_->word_counts_by_topic_[k] > 0) {
      likelihood += lg_etaW;
      likelihood -= lgamma(lda_state_->word_counts_by_topic_[k] + etaW);
      for (int w = 0; w < lda_state_->size_vocab_; ++w) {
        if (lda_state_->topic_lambda_[k][w] > 0) {
          likelihood -= lg_eta;
          likelihood += lgamma(lda_state_->topic_lambda_[k][w] + lda_state_->eta_);
        }
      }
    }
  }
  return likelihood;
}

void LDA::save_state(const char* name) {
  lda_state_->save_lda_state(name);
}

void LDA::load_state(const char* name) {
  lda_state_ = new LDAState();
  lda_state_->load_lda_state(name);
}

void LDA::init_fast_gibbs_sampling_variables() {
  unique_topic_by_word_.resize(lda_state_->size_vocab_);
  smoothing_prob_.resize(lda_state_->word_counts_by_topic_.size(), lda_state_->alpha_/(lda_state_->eta_ * lda_state_->size_vocab_));
  smoothing_prob_sum_ = lda_state_->num_topics_ * lda_state_->alpha_/(lda_state_->eta_ * lda_state_->size_vocab_);
  vct_ptr_resize(&doc_prob_, lda_state_->word_counts_by_topic_.size(), num_docs_);
  doc_prob_sum_.resize(num_docs_, 0.0);
  unique_topic_by_doc_.resize(num_docs_);
}

void LDA::save_doc_states(const char* name) {
  char filename[500];
  sprintf(filename, "%s.doc.states", name);
  FILE* doc_state_file = fopen(filename, "w");
  for (int d = 0; d < num_docs_; ++d) {
    fprintf(doc_state_file, "%d", word_counts_by_topic_doc_[0][d]);
    for (int k = 1; k < lda_state_->num_topics_; ++k) {
      fprintf(doc_state_file, " %d", word_counts_by_topic_doc_[k][d]);
    }
    fprintf(doc_state_file, "\n");
  }
  fclose(doc_state_file);
}

