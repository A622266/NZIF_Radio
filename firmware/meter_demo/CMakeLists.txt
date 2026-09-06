cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(nzif_meter_demo C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

# The metering algorithms are shared with the host-side harness and are not
# duplicated here — meter.c compiles straight into the firmware.
set(METER_DIR ${CMAKE_CURRENT_LIST_DIR}/../../nzif/meter_display)

# Two interchangeable face renderers, both implementing face.h:
#
#   face_pic.c    background artwork in panel flash; needle erased with picq.
#                 Prettier, and much less code. Needs the .tft to carry the
#                 generated PNG as picture ID 0.
#   face_drawn.c  scale drawn at runtime over a flat amber fill. Needs nothing
#                 in the .tft but a black page. Kept as the fallback that is
#                 already known to work on hardware.
option(METER_FACE_ARTWORK "Use the stored background picture for the face" ON)

if(METER_FACE_ARTWORK)
    set(FACE_SRC face_pic.c)
else()
    set(FACE_SRC face_drawn.c strokefont.c)
endif()

add_executable(nzif_meter_demo
    main.c
    nextion.c
    ${FACE_SRC}
    ${METER_DIR}/meter.c
)

target_include_directories(nzif_meter_demo PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
    ${METER_DIR}
)

target_link_libraries(nzif_meter_demo
    pico_stdlib
    hardware_uart
)

# stdio must NOT go to UART: uart0 is wired to the Nextion.
pico_enable_stdio_usb(nzif_meter_demo 1)
pico_enable_stdio_uart(nzif_meter_demo 0)

pico_add_extra_outputs(nzif_meter_demo)
