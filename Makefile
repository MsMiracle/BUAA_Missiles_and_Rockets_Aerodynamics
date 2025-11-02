# Makefile - portable build using gcc/cc when available

# Compiler selection:
# - If the environment provides CC it will be used.
# - Otherwise prefer `gcc` if present, then fall back to `cc`.
ifeq ($(origin CC), undefined)
  ifneq ($(shell command -v gcc 2>/dev/null),)
    CC := gcc
  else ifneq ($(shell command -v cc 2>/dev/null),)
    CC := cc
  else
    $(error No suitable C compiler found. Install gcc or set CC in the environment.)
  endif
endif

SRCDIR := source
INCDIR := include
CFLAGS ?= -g -Wall -Wextra -I$(INCDIR)
BUILDDIR := build
OBJDIR := $(BUILDDIR)/obj

SRCS := $(wildcard $(SRCDIR)/*.c)
OBJS := $(patsubst $(SRCDIR)/%.c,$(OBJDIR)/%.o,$(SRCS))

# Add .exe suffix on Windows (when using natively on Windows/MinGW)
ifeq ($(OS),Windows_NT)
  EXE := .exe
else
  EXE :=
endif

TARGET := $(BUILDDIR)/sim$(EXE)

.PHONY: all clean run dirs help

all: dirs $(TARGET)

dirs:
ifeq ($(OS),Windows_NT)
	@if not exist "$(BUILDDIR)" mkdir "$(BUILDDIR)"
	@if not exist "$(OBJDIR)" mkdir "$(OBJDIR)"
else
	@mkdir -p $(BUILDDIR) $(OBJDIR)
endif

$(TARGET): $(OBJS)
	@echo "Linking $@ with $(CC)"
	$(CC) $(CFLAGS) $^ -o $@ -lm

$(OBJDIR)/%.o: $(SRCDIR)/%.c | dirs
	@echo "Compiling $<"
	$(CC) $(CFLAGS) -c $< -o $@

run: all
	@echo "Running $(TARGET) ..."
	@./$(TARGET)

clean:
	@rm -rf $(BUILDDIR)

help:
	@echo "Usage: make [target]"
	@echo "Targets: all (default), run, clean, help"

# Useful info
# Sources: $(SRCS)
# To build: run `make`
# To run:   run `make run` (or ./build/sim)