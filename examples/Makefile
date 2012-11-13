TARGET = test.bin
OBJECTS = vectors.obj printString.obj

AS := ../assemble.py 
LD := ../link.py

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(LD) -o $@ $^

%.obj: %.vm32
	$(AS) -o $@ $<

clean:
	rm -f *.obj *.bin

.PHONY: clean
