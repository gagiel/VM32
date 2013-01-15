TARGET = test.bin
OBJECTS = vectors.obj printString.obj

AS := ../assemble.py 
LD := ../link.py

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(LD) -d -o $@ $^

%.obj: %.vm32
	$(AS) -d -o $@ $<

clean:
	rm -f *.obj *.bin

.PHONY: clean
