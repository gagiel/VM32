SUBTARGETS = hvtest printString timerTest twovms addprint

DIRS = $(SUBTARGETS:%=%.dir)

%.dir:
	@make --no-print-directory -C $* all

all: $(DIRS)

clean:
	@-for i in $(SUBTARGETS); do \
		make --no-print-directory -C $$i clean; \
	done

.PHONY: clean all
