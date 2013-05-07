TARGET = test.bin
OBJECTS = addprint.obj

AS := ../../assemble.py 
LD := ../../link.py

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(LD) -o $@ -m $@.map $^

%.obj: %.vm32
	$(AS) -o $@ $<

clean:
	rm -f *.obj *.bin *.map

.PHONY: clean all
