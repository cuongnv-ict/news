CC = g++ -Wall
#CC = g++ -ansi -Wall -pedantic
#CFLAGS = -g -Wall -O3 -ffast-math -DHAVE_INLINE -DGSL_RANGE_CHECK_OFF
# CFLAGS = -g -Wall
LDFLAGS = -lgsl -lm -lgslcblas #-latlas

GSL_INCLUDE = /home/nobita/gsl/include/
GSL_LIB = /home/nobita/gsl/lib/

GSL_INCLUDE_MAC = /home/nobita/gsl/include/
GSL_LIB_MAC = /home/nobita/gsl/lib/

LSOURCE = main.cpp utils.cpp corpus.cpp state.cpp
LHEADER = utils.h corpus.h state.h

mac: $(LSOURCE) $(HEADER)
	  $(CC) -I$(GSL_INCLUDE_MAC) -L$(GSL_LIB_MAC) $(LSOURCE) -o lda $(LDFLAGS)

mac-d: $(LSOURCE) $(HEADER)
	  $(CC) -g -I$(GSL_INCLUDE_MAC) -L$(GSL_LIB_MAC) $(LSOURCE) -o lda $(LDFLAGS)

linux: $(LSOURCE) $(HEADER)
	  $(CC) -I$(GSL_INCLUDE) -L$(GSL_LIB) $(LSOURCE) -o lda $(LDFLAGS)

linux-d: $(LSOURCE) $(HEADER)
	  $(CC) -g -I$(GSL_INCLUDE) -L$(GSL_LIB) $(LSOURCE) -o lda $(LDFLAGS)


clean:
	-rm lda
