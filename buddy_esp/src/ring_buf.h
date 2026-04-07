#pragma once

#include "freertos/ringbuf.h"

extern RingbufHandle_t ring_buffer;

void ring_buffer_init(void);