# Pico SDK import helper
# Expects PICO_SDK_PATH to be set in the environment.

include_guard()

if (DEFINED ENV{PICO_SDK_PATH})
    set(PICO_SDK_PATH $ENV{PICO_SDK_PATH})
endif()

if (NOT PICO_SDK_PATH)
    message(FATAL_ERROR "PICO_SDK_PATH is not set. Set it to your Pico SDK path.")
endif()

include(${PICO_SDK_PATH}/external/pico_sdk_init.cmake)
