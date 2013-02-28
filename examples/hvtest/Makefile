TARGET = hv.bin
OBJECTS = vectors.obj hv.obj vm1.obj

AS := ../../assemble.py
LD := ../../link.py

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(LD) -o $@ $^

%.obj: %.vm32
	$(AS) -o $@ $<

clean:
	rm -f *.obj *.bin

.PHONY: clean all
