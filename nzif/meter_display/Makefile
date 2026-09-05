# Host build of the NZIF panel meter exercise harness.
#
#   make        build the harness
#   make run    build and run it
#   make clean
#
# meter.c/meter.h are the code intended for the Pico; meter_sim.c is host-only
# scaffolding. Nothing here needs the Pico SDK.
#
# On Windows, pass a compiler explicitly, since there is no `cc`:
#
#   mingw32-make CC=clang
#
# Or skip make entirely — it is only two files:
#
#   clang -std=c99 -Wall -Wextra -Wpedantic -O2 -o meter_sim.exe meter.c meter_sim.c -lm

CFLAGS  ?= -std=c99 -Wall -Wextra -Wpedantic -O2
LDLIBS  := -lm

# Windows needs an .exe suffix and has no rm/./ — detect and adjust.
ifeq ($(OS),Windows_NT)
  EXE   := .exe
  RM_F  := del /Q /F
  RUN   :=
  FIXP   = $(subst /,\,$1)
else
  EXE   :=
  RM_F  := rm -f
  RUN   := ./
  FIXP   = $1
endif

TARGET  := meter_sim$(EXE)
OBJS    := meter.o meter_sim.o

.PHONY: all run clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDLIBS)

meter.o: meter.c meter.h
	$(CC) $(CFLAGS) -c -o $@ $<

meter_sim.o: meter_sim.c meter.h
	$(CC) $(CFLAGS) -c -o $@ $<

run: $(TARGET)
	$(RUN)$(TARGET)

clean:
	-$(RM_F) $(call FIXP,$(TARGET) $(OBJS))
