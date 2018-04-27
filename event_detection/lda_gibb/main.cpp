#include <libgen.h>
#include <string.h>
#include "corpus.h"
#include "state.h"
#include "utils.h"

gsl_rng * RANDOM_NUMBER = NULL;

void print_usage_and_exit() {
  // print usage information

  printf("\nC++ implementation of Gibbs sampling for latent Dirichlet allocation, a faster version.\n");
  printf("Authors: Chong Wang, chongw@cs.princeton.edu, Computer Science Department, Princeton University.\n");

  printf("usage:\n");
  printf("      lda               [options]\n");
  printf("      --help:           print help information.\n");
  printf("      --verbose:        print running information.\n");
  printf("\n");

  printf("      control parameters:\n");
  printf("      --directory:       the saving directory, required.\n");
  printf("      --random_seed:     the random seed, default from the current time.\n");
  printf("      --max_iter:        the max number of iterations, default 100 (-1 means infinite).\n");
  printf("      --max_time:        the max time allowed (in seconds), default 1800 (-1 means infinite).\n");
  printf("      --save_lag:        the saving point, default 5.\n");
  printf("\n");

  printf("      data parameters:\n");
  printf("      --train_data:      the training data file/pattern, in lda-c format.\n");
  printf("\n");

  printf("      model parameters:\n");
  printf("      --eta:             the topic Dirichlet parameter, default 0.01.\n");
  printf("      --alpha:           the topic proportion Dirichlet, default 0.1.\n");
  printf("      --num_topics:      the number of topics, default 100.\n");

  printf("\n");

  printf("      test only parameters:\n");
  printf("      --test_data:       the test data file/pattern, in lda-c format.\n");
  printf("      --model_prefix:    the model_prefix.\n");

  printf("*******************************************************************************************************\n");

  exit(0);
}

int main(int argc, char* argv[]) {
  if (argc < 2) print_usage_and_exit();

  int verbose = 0;

  // Control parameters.
  char*  directory = NULL;
  time_t t; time(&t);
  long   random_seed = (long) t;
  int    max_iter = 100;
  int    max_time = 1800;
  int    save_lag = 5;

  // Data parameters.
  char* train_data = NULL;

  // Model parameters.
  double eta = 0.01;
  double alpha = 0.1;
  int num_topics = 100;

  // test only parameters
  char* test_data = NULL;
  char* model_prefix = NULL;

  for (int i = 1; i < argc; ++i) {
    if (!strcmp(argv[i], "--help")) print_usage_and_exit();
    else if (!strcmp(argv[i], "--verbose"))        verbose = 1;

    else if (!strcmp(argv[i], "--directory"))       directory = argv[++i];
    else if (!strcmp(argv[i], "--random_seed"))     random_seed = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--max_iter"))        max_iter = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--max_time"))        max_time = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--save_lag"))        save_lag = atoi(argv[++i]);

    else if (!strcmp(argv[i], "--train_data"))      train_data = argv[++i];

    else if (!strcmp(argv[i], "--eta"))             eta = atof(argv[++i]);
    else if (!strcmp(argv[i], "--alpha"))           alpha = atof(argv[++i]);
    else if (!strcmp(argv[i], "--num_topics"))      num_topics = atoi(argv[++i]);

    else if (!strcmp(argv[i], "--test_data"))       test_data = argv[++i];
    else if (!strcmp(argv[i], "--model_prefix"))    model_prefix = argv[++i];
    else {
      printf("%s, unknown parameters, exit\n", argv[i]); 
      print_usage_and_exit();
    }
  }
  /// print information
  // printf("************************************************************************************************\n");

  if (directory == NULL)  {
    printf("Following information is missing: --directory\n");
    printf("Run ./lda for help.\n");
    exit(0);
  }
  
  if (!dir_exists(directory)) make_directory(directory);
  // printf("Working directory: %s.\n", directory);

  char name[500];
  // Init random numbe generator.
  RANDOM_NUMBER = new_random_number_generator(random_seed);
  
  if (test_data == NULL || model_prefix == NULL) {
    sprintf(name, "%s/settings.dat", directory);
    // printf("Setting saved at %s.\n", name); 
    FILE* setting_file = fopen(name, "w");

    fprintf(setting_file, "Control parameters:\n");
    fprintf(setting_file, "directory: %s\n", directory);
    fprintf(setting_file, "random_seed: %d\n", (int)random_seed);
    fprintf(setting_file, "save_lag: %d\n", save_lag);
    fprintf(setting_file, "max_iter: %d\n", max_iter);
    fprintf(setting_file, "max_time: %d\n", max_time);

    fprintf(setting_file, "\nData parameters:\n");
    fprintf(setting_file, "train_data: %s\n", train_data);

    fprintf(setting_file, "\nModel parameters:\n");
    fprintf(setting_file, "eta: %.4lf\n", eta);
    fprintf(setting_file, "alpha: %.4lf\n", alpha);
    fprintf(setting_file, "num_topics: %d\n", num_topics);

    fclose(setting_file);

    Corpus* c_train = NULL;

    // printf("Reading training data from %s.\n", train_data);
    // Reading one of the train data.
    c_train = new Corpus();
    c_train->read_data(train_data);

    // Open the log file for training data.
    sprintf(name, "%s/train.log", directory);
    FILE* train_log = fopen(name, "w");
    // Heldout columns record the documents that have not seen before.
    sprintf(name, "time\titer\tword.count\tlikelihood\tavg.likelihood");
    if(verbose) printf("%s\n", name);
    fprintf(train_log, "%s\n", name);
    
    // Start iterating.
    time_t start, current;
    int total_time = 0;
    int iter = 0;

    LDA* lda = new LDA();
    lda->init_lda(eta, alpha, num_topics, c_train->size_vocab_);

    // Setting up the lda state.
    lda->setup_doc_states(c_train->docs_);
    // first iteration
    lda->iterate_gibbs_state(false, false);

    while ((max_iter == -1 || iter < max_iter) && (max_time == -1 || total_time < max_time)) {
      ++iter;
      time (&start);
      // printf("\rIter = %d", iter);
      fflush(stdout); 
      // Iterations.
      lda->iterate_gibbs_state(true, true);
      // Scoring the documents.
      double likelihood = lda->log_likelihood(NULL);
      
      // Record the time.
      time(&current);
      int elapse = (int) difftime(current, start);
      total_time += elapse;

      sprintf(name, "%d\t%d\t%d\t\t%.3f\t%.5f", 
              total_time, iter, c_train->num_total_words_, likelihood, likelihood/c_train->num_total_words_);

      if (verbose) printf("%s\n", name);
      fprintf(train_log, "%s\n", name); 
      fflush(train_log);

      if (save_lag > 0 && (iter % save_lag == 0)) {
        sprintf(name, "%s/iter@%05d", directory, iter);
        lda->save_state(name);
        lda->save_doc_states(name);
      }
    }

    sprintf(name, "%s/final", directory);
    lda->save_state(name);
    lda->save_doc_states(name);

    // Free training data.
    if (c_train != NULL) {
      delete c_train;
    }
    fclose(train_log);

    delete lda;
  }
  
  if (test_data != NULL && model_prefix != NULL) {
    Corpus* c_test = new Corpus();
    c_test->read_data(test_data);

    LDA* lda = new LDA();
    printf("Loading model from prefix %s...\n", model_prefix);
    lda->load_state(model_prefix);

    // Remember the old state.
    LDAState* old_lda_state = new LDAState();
    old_lda_state->copy_lda_state(*lda->lda_state_);

    lda->setup_doc_states(c_test->docs_);
    lda->setup_unique_topic_by_word_(); 

    if (verbose) printf("Initialization ...\n");
    lda->iterate_gibbs_state(false, false);

    sprintf(name, "%s/%s-test.log", directory, basename(model_prefix));
    FILE* test_log = fopen(name, "w");
    sprintf(name, "time\titer\tword.count\tlikelihood\tavg.likelihood");
    if(verbose) printf("%s\n", name);
    fprintf(test_log, "%s\n", name);

    time_t start, current;
    int total_time = 0;
    int iter = 0;

    // Iterations.
    while ((max_iter == -1 || iter < max_iter) && (max_time == -1 || total_time < max_time)) {
      ++iter;
      time (&start);
      lda->iterate_gibbs_state(true, true);
      double likelihood = lda->log_likelihood(old_lda_state);
      time(&current);
      int elapse = (int) difftime(current, start);
      total_time += elapse;

      sprintf(name, "%d\t%d\t%d\t\t%.3f\t%.5f", 
              total_time, iter, c_test->num_total_words_, likelihood,
              likelihood/c_test->num_total_words_);

      if (verbose) printf("%s\n", name);
      fprintf(test_log, "%s\n", name); 
      fflush(test_log);
    }
    
    if (verbose) printf("Done and saving ...\n");
    sprintf(name, "%s/%s-test", directory, basename(model_prefix));
    lda->save_state(name);
    lda->save_doc_states(name);
    fclose(test_log);

    delete lda;
    delete old_lda_state;
    delete c_test;
  }

  // Free random number generator.
  free_random_number_generator(RANDOM_NUMBER);
  return 0;
}
