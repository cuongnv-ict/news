The LDA code is provided under the "lda" directory.

For example, run LDA with parameters - 50 topics - the topic Dirichlet set to 0.01 - the topic proportion Dirichlet set to 0.1 as follows:

./lda --directory fit_50/ --train_data ~/arxiv/dat/mult_lda.dat --num_topics 50 --eta 0.01 --alpha 0.1 --max_iter -1 --max_time -1

mult_lda.dat contains the documents (see the David Blei's lda-c package for the exact format: http://www.cs.columbia.edu/~blei/lda-c/index.html)

Note The values of eta and alpha need to reflect those used when loading the LDA fits in CTPF (see collabtm.cc:initialize()).

The output directory ("fit_50/" in the above example) will contain the fit files which can be used to initialize CTPF with -lda-init option. Specifically *.topics corresponds to beta-lda-k.tsv, and *.doc.states corresponds to theta-lda-k.tsv.