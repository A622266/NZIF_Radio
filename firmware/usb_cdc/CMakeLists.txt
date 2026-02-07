cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(nzif_usb_cdc C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(nzif_usb_cdc
    main.c
)

target_link_libraries(nzif_usb_cdc
    pico_stdlib
    tinyusb_device
)

pico_enable_stdio_usb(nzif_usb_cdc 1)
pico_enable_stdio_uart(nzif_usb_cdc 0)

pico_add_extra_outputs(nzif_usb_cdc)
