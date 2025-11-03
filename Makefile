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
LDFLAGS ?=
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

# Optional OpenMP support: enable with `make OMP=1`
OMP ?= 0
ifeq ($(OMP),1)
	CCVERSION := $(shell $(CC) --version 2>/dev/null)
  ifneq (,$(findstring clang,$(CCVERSION)))
    # Clang on macOS needs Homebrew's libomp path
    LOMP_PREFIX := $(shell brew --prefix libomp 2>/dev/null)
    ifneq ($(LOMP_PREFIX),)
      CFLAGS += -Xpreprocessor -fopenmp -I$(LOMP_PREFIX)/include
      LDFLAGS += -L$(LOMP_PREFIX)/lib -lomp
    else
      # Fallback if brew or libomp is not found
      CFLAGS += -Xpreprocessor -fopenmp
      LDFLAGS += -lomp
    endif
  else
    # GCC and compatibles
    CFLAGS += -fopenmp
    LDFLAGS += -fopenmp
  endif
endif

dirs:
ifeq ($(OS),Windows_NT)
	@if not exist "$(BUILDDIR)" mkdir "$(BUILDDIR)"
	@if not exist "$(OBJDIR)" mkdir "$(OBJDIR)"
else
	@mkdir -p $(BUILDDIR) $(OBJDIR)
endif

$(TARGET): $(OBJS)
	@echo "Linking $@ with $(CC)"
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS) -lm

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