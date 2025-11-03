# CMakeLists.txt for the CFD Simulation

# 1. Project Setup
cmake_minimum_required(VERSION 3.15)
project(cfd_sim C)

# Set C standard for portability
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# 2. Project Structure and Executable Definition
# Add the 'include' directory to the include path
include_directories(include)

# Automatically find all .c files in the 'source' directory
file(GLOB SOURCES "source/*.c")

# Define the executable target
add_executable(${PROJECT_NAME} ${SOURCES})

# 3. Configuration Options & Target Properties
# Add an option to enable/disable OpenMP, defaulting to ON
option(USE_OMP "Enable OpenMP for parallel execution" ON)

# Find and apply OpenMP if enabled
if(USE_OMP)
    find_package(OpenMP QUIET)
    if(OpenMP_FOUND)
        message(STATUS "OpenMP found via CMake package. Enabling parallel support.")
        target_link_libraries(${PROJECT_NAME} PRIVATE OpenMP::OpenMP_C)
    else()
        # Fallback for Apple Clang with Homebrew libomp
        if(APPLE)
            execute_process(
                COMMAND brew --prefix libomp
                OUTPUT_VARIABLE BREW_LIBOMP_PREFIX
                OUTPUT_STRIP_TRAILING_WHITESPACE
                ERROR_QUIET
            )
            if(BREW_LIBOMP_PREFIX)
                message(STATUS "OpenMP not found by CMake. Using Homebrew libomp at ${BREW_LIBOMP_PREFIX}")
                target_include_directories(${PROJECT_NAME} PRIVATE ${BREW_LIBOMP_PREFIX}/include)
                # Clang needs these compile flags to enable OpenMP
                target_compile_options(${PROJECT_NAME} PRIVATE -Xpreprocessor -fopenmp)
                # Link against libomp from Homebrew
                target_link_directories(${PROJECT_NAME} PRIVATE ${BREW_LIBOMP_PREFIX}/lib)
                target_link_libraries(${PROJECT_NAME} PRIVATE omp)
            else()
                message(WARNING "OpenMP not found and Homebrew libomp not detected. Building in single-threaded mode.")
            endif()
        else()
            message(WARNING "OpenMP not found. Building in single-threaded mode.")
        endif()
    endif()
endif()

# Link the math library (for functions like pow, etc.)
target_link_libraries(${PROJECT_NAME} PRIVATE m)

# 4. Output Configuration
# Set the output name for the executable to 'sim'
set_target_properties(${PROJECT_NAME} PROPERTIES OUTPUT_NAME "sim")

# Place the final executable directly in the top-level build directory
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

# 5. Informative Messages
message(STATUS "Project: ${PROJECT_NAME}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "To build, run: cmake --build .")
